# Vertex AI setup and cost safety

## One-time setup

1. Create a **dedicated** Google Cloud project for image generation, so its billing, permissions, quotas and kill switch are separate from anything in production.
2. Enable billing and the Vertex AI API (`aiplatform.googleapis.com`). The caller needs `roles/aiplatform.user`.
3. Install the dependencies and sign in with Application Default Credentials:

```bash
python -m pip install -r requirements.txt
gcloud auth application-default login
```

4. Point the script at the project:

```bash
# macOS / Linux
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="global"
```

```powershell
# Windows PowerShell
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
$env:GOOGLE_CLOUD_LOCATION = "global"
```

Do not create a long-lived API key for this workflow, and never copy the ADC credentials file anywhere.

## Models

| Model | Use | Max reference images |
|---|---|---|
| `gemini-3.1-flash-image` | default for drafts and batches; 512, 1K, 2K, 4K (preview) | 14 |
| `gemini-3-pro-image` | finals, complex multi-reference work; 1K, 2K, 4K (preview) | 14 |

Iterate at 2K. Keep 4K for an approved final.

## Cost safeguards

1. **Dedicated project**, as above.
2. **Preview by default.** `generate.py` writes `request.json` and spends nothing unless `--execute` is given.
3. **Local request limits.** 10 live requests per UTC day and 50 per UTC month by default, counted in a local ledger (`%LOCALAPPDATA%\product-photo-studio\usage.jsonl` on Windows, `~/.local/state/product-photo-studio/usage.jsonl` elsewhere). Override with `PHOTO_STUDIO_DAILY_LIMIT` / `PHOTO_STUDIO_MONTHLY_LIMIT` or the CLI flags. Lowering is always fine; raising is the user's decision.
4. **4K gate.** Live 4K also needs `--allow-4k`.
5. **Google quotas.** Inspect the quotas available for your model and project. Some models use shared capacity and do not expose a configurable daily request quota. Where supported, quotas limit throughput rather than total spend.
6. **Budget alerts.** Configure alerts for the dedicated project. A Cloud Billing budget does not stop billing. Do not treat this script or a budget alert as an account-wide money limit.

## Prices

Output-image prices verified on 2026-10-20 (USD per image): Flash 0.045 at 512, 0.067 at 1K, 0.101 at 2K, 0.15 at 4K; Pro 0.134 at 1K/2K, 0.24 at 4K. Input images and text are billed on top. The script's estimate covers the output image only. Check the current Vertex AI pricing page before changing limits.

## Errors you will meet

| Symptom | Likely cause | Fix |
|---|---|---|
| 403 / permission denied | API not enabled or missing `roles/aiplatform.user` | enable the API, grant the role |
| 429 resource exhausted | model quota or shared capacity | wait and retry later, or switch to the other model |
| no image, only text | the safety filter blocked the request | read `response.txt`, remove the trigger (often brand names or people) |
| "reached daily limit" | the local ledger did its job | wait for the next UTC day or ask the user |

The ledger reserves each attempt before sending and blocks concurrent reservations with an atomic lock folder. A corrupt ledger stops execution. Failed requests still count. Do not change the ledger path to evade limits. Counters cover only this ledger on this machine, and the price estimate excludes input and text/reasoning charges. SDK retries are disabled.

Verified sources (2026-10-20): [Flash model](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-1-flash-image), [Pro model](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image), [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing). Check pricing and availability before paid execution.
