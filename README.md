# Elvebredd Value API

Pulls Adopt Me values from [elvebredd.com](https://elvebredd.com) and serves them as JSON.

The calculator page embeds the full item list (every pet + all neon/mega and potion variants) in its Next.js payload, so one request gets everything. Cloudflare 403s plain curl/requests; `curl_cffi` with Chrome impersonation gets through. Results are cached in memory for 10 min (`ELVEBREDD_CACHE_TTL`).

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn server:app --port 8040
```

Docs at http://127.0.0.1:8040/docs

## Endpoints

- `GET /api/pets` (`?q=dragon` to search)
- `GET /api/pets/{name}` e.g. `/api/pets/shadow-dragon` (name, slug, or id)
- `GET /api/items?type=toys&q=` (types: pets, pet wear, toys, stickers, vehicles, strollers, food, gifts, eggs, other)
- `GET /api/items/{name}`
- `GET /api/value?name=shadow-dragon&age=mega&potion=fly_ride` (age: default|neon|mega, potion: nopotion|ride|fly|fly_ride)
- `POST /api/refresh` force re-scrape

Pet shape: `values.{default,neon,mega}.{base,nopotion,ride,fly,fly_ride}`. Non-pet items have a single `value`.
