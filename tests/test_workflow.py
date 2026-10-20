"""Offline checks for request accounting and the public example."""
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/product-photo-studio/skills/product-photo-studio"
spec = importlib.util.spec_from_file_location("generate", SKILL / "scripts/generate.py")
generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate)


class WorkflowTests(unittest.TestCase):
    def test_preview_needs_no_sdk_or_credentials_and_does_not_spend(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            ledger = base / "usage.jsonl"
            result = subprocess.run([
                sys.executable, "-S", str(SKILL / "scripts/generate.py"),
                "--prompt", "A ceramic mug", "--output-dir", str(base / "out"),
                "--usage-ledger", str(ledger),
            ], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["dry_run"])
            self.assertFalse(ledger.exists())

    def test_attempts_consume_daily_and_monthly_limits_even_without_success(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "usage.jsonl"
            generate.reserve_attempt(ledger, 1, 10, {"model": "test"})
            with self.assertRaisesRegex(SystemExit, "Daily request limit"):
                generate.reserve_attempt(ledger, 1, 10, {})
            with self.assertRaisesRegex(SystemExit, "Monthly request limit"):
                generate.reserve_attempt(ledger, 10, 1, {})

    def test_concurrent_reservations_cannot_exceed_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "usage.jsonl"
            def attempt(_):
                try:
                    generate.reserve_attempt(ledger, 1, 1, {})
                    return True
                except SystemExit:
                    return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(attempt, range(16)))
            self.assertEqual(sum(outcomes), 1)
            self.assertEqual(generate.attempted_counts(ledger, datetime.now(timezone.utc)), (1, 1))

    def test_corrupt_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "usage.jsonl"
            ledger.write_text('{"event":', encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "Invalid usage ledger"):
                generate.reserve_attempt(ledger, 10, 50, {})

    def test_live_4k_is_blocked_before_sdk_import(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([
                sys.executable, "-S", str(SKILL / "scripts/generate.py"),
                "--prompt", "A mug", "--output-dir", folder,
                "--project", "example-project", "--execute", "--image-size", "4K",
                "--usage-ledger", str(Path(folder) / "ledger.jsonl"),
            ], capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Live 4K is blocked", result.stderr)
            self.assertFalse((Path(folder) / "ledger.jsonl").exists())

    def test_paid_path_reserves_before_call_and_saves_output_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            ledger = base / "usage.jsonl"
            google = ModuleType("google")
            genai = ModuleType("google.genai")
            types = SimpleNamespace(
                HttpOptions=lambda **kw: kw, HttpRetryOptions=lambda **kw: kw,
                GenerateContentConfig=lambda **kw: kw, ImageConfig=lambda **kw: kw,
                Modality=SimpleNamespace(TEXT="TEXT", IMAGE="IMAGE"),
            )
            genai.types = types
            google.genai = genai
            def respond(**kwargs):
                self.assertEqual(generate.attempted_counts(ledger, datetime.now(timezone.utc)), (1, 1))
                return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[
                    SimpleNamespace(text=None, inline_data=SimpleNamespace(data=b"test-image", mime_type="image/png"))
                ]))])
            client = Mock()
            client.models.generate_content.side_effect = respond
            genai.Client = Mock(return_value=client)
            pil = ModuleType("PIL")
            pil.Image = Mock()
            args = ["generate.py", "--prompt", "A mug", "--project", "example-project",
                    "--output-dir", str(base / "out"), "--usage-ledger", str(ledger), "--execute"]
            with patch.dict(sys.modules, {"google": google, "google.genai": genai, "PIL": pil}), patch.object(sys, "argv", args), patch("builtins.print"):
                generate.main()
            self.assertEqual(genai.Client.call_args.kwargs["http_options"]["retry_options"]["attempts"], 1)
            client.models.generate_content.assert_called_once()
            self.assertEqual((base / "out/generated-01.png").read_bytes(), b"test-image")
            self.assertEqual([item["event"] for item in generate.read_ledger(ledger)], ["attempted", "completed"])

    def test_example_prompt_matches_and_references_stay_in_order(self):
        example = SKILL / "examples/orange-lens-eyewear"
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([
                sys.executable, str(SKILL / "scripts/build_prompt.py"),
                str(example / "job.toml"), "--out", folder,
            ], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((Path(folder) / "job.json").read_text(encoding="utf-8"))
            self.assertEqual([ref["slot"] for ref in manifest["references"]], ["product", "color_lock", "logo"])
            prompt = (Path(folder) / "prompt.txt").read_text(encoding="utf-8")
            self.assertNotIn("{{", prompt)
            self.assertEqual(prompt, (example / "prompt.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
