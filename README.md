# Adopt Me Value API

Free, open Adopt Me pet and item values sourced from [elvebredd.com](https://elvebredd.com). No key needed, CORS open.

**Base URL:** https://elvebredd-value-api.vercel.app · **Docs:** https://elvebredd-value-api.vercel.app/docs

## Endpoints

- `GET /api/pets` (`?q=dragon` to search)
- `GET /api/pets/{name}` e.g. `/api/pets/shadow-dragon` (name, slug, or id)
- `GET /api/items?type=toys&q=` and `GET /api/items/{name}`
- `GET /api/types`
- `GET /api/value?name=shadow-dragon&age=mega&potion=fly_ride` (age: default|neon|mega, potion: nopotion|ride|fly|fly_ride)

Pets have `values.{default,neon,mega}.{base,nopotion,ride,fly,fly_ride}`; other items have a single `value`. Every list response includes `updated_at` (unix time).

## How it works

- `scraper.py` runs every 15 min in GitHub Actions (`.github/workflows/scrape.yml`), pulls the full item list embedded in elvebredd's calculator page (curl_cffi Chrome impersonation gets past Cloudflare), and commits `data/values.json` only when values change.
- `server.py` (FastAPI on Vercel) only reads that JSON from GitHub raw, never elvebredd. Responses are edge-cached 5 min.

## Local

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-scraper.txt uvicorn
.venv/bin/python scraper.py          # refresh data/values.json
.venv/bin/uvicorn server:app --port 8040
```

Deploy: `npx vercel --prod --yes` (not git-connected).
