# JanSetu AI — PS5 hackathon prototype

An unofficial, mobile-responsive government scheme eligibility explorer with a guided rule-based conversation, official source links, browser speech input/output where supported, and no persistent collection of citizen profiles.

## Running locally
```bash
pip install -r requirements.txt
python -m pytest -q
uvicorn app:app --reload
```
Open http://localhost:8000 and check http://localhost:8000/api/health.

## Render backend
Connect this GitHub repo to Render, create a **Blueprint** using `render.yaml` or a Python Web Service using:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`

The Render origin also serves the HTML frontend directly.

## Cloudflare Pages frontend
Connect this **same repository** to **Cloudflare Pages** (not standalone Workers). Choose framework **None**, root directory repository root, leave build command blank, and set output directory `static`. Configure **RENDER_API_URL** in Pages production/preview environment variables as the Render HTTPS origin without trailing `/api`. Redeploy and test `https://YOUR-SITE.pages.dev/api/health`.

The `functions/api/[[path]].js` Pages Function proxies same-origin frontend API calls to Render.

## Important limitations
- Five curated scheme records, **not yet** the PDF requirement of 20–30 fully source-verified schemes.
- Eligibility is only a preliminary rule-check and **never** an official entitlement determination. Additional exclusions and program-specific rules may apply; verify all scheme data on the linked official portals.
- Speech relies on browser-provided SpeechRecognition and speechSynthesis APIs. Indian-language end-to-end success has **not** yet been verified; prompts are in English. No machine translation is implemented.
- No multilingual RAG/embeddings, LLM grounding, tested Hindi/Tamil/Kannada demo, or speech accuracy benchmarks yet.
- No Aadhaar numbers, bank details or OTPs are requested. Inputs are processed without persistent profile storage.

This repository is a **deployable foundation**, not a complete PS5 submission. Check official sources before showing benefits or eligibility to the public. Not affiliated with the Government of India.
