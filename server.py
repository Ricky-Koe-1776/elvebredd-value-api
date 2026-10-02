import json
import os
import threading
import time
import urllib.request

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from scraper import AGES, POTIONS, slugify

DATA_URL = os.environ.get(
    "DATA_URL",
    "https://raw.githubusercontent.com/Ricky-Koe-1776/elvebredd-value-api/main/data/values.json",
)
LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "values.json")
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))

app = FastAPI(
    title="Adopt Me Value API",
    version="1.0",
    description=(
        "Free Adopt Me pet and item values sourced from elvebredd.com. Updated every 15 minutes. "
        "No key needed, CORS open.\n\nTry: `/api/value?name=shadow-dragon&age=mega&potion=fly_ride`"
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

_lock = threading.Lock()
_cache = {"snap": None, "at": 0}


@app.middleware("http")
async def cdn_cache(request, call_next):
    resp = await call_next(request)
    if request.method == "GET" and resp.status_code == 200 and request.url.path != "/":
        # let the vercel edge serve repeat requests instead of the function
        resp.headers["Cache-Control"] = "public, s-maxage=300, stale-while-revalidate=600"
    return resp


def load_remote():
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "adoptme-value-api"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def snapshot():
    with _lock:
        if _cache["snap"] is None or time.time() - _cache["at"] > CACHE_TTL:
            try:
                _cache["snap"] = load_remote()
            except Exception:
                if _cache["snap"] is None:
                    try:
                        with open(LOCAL_PATH) as f:
                            _cache["snap"] = json.load(f)
                    except OSError:
                        raise HTTPException(503, "values not available yet")
            _cache["at"] = time.time()
        return _cache["snap"]


def find_item(name, item_type=None):
    slug = slugify(name)
    items = snapshot()["items"]
    if item_type:
        items = [i for i in items if i["type"] == item_type]
    for i in items:
        if i["slug"] == slug or str(i["id"]) == name:
            return i
    raise HTTPException(404, f"no item matching '{name}'")


@app.get("/")
def root(request: Request):
    # people opening the base url in a browser land on the docs, scripts still get json
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/docs")
    snap = snapshot()
    return {
        "name": "Adopt Me Value API",
        "source": "https://elvebredd.com",
        "docs": "/docs",
        "count": snap["count"],
        "updated_at": snap["updated_at"],
        "endpoints": {
            "/api/pets": "all pets, ?q= to search",
            "/api/pets/{name}": "one pet by name, slug, or id",
            "/api/items": "all items, ?type= and ?q= filters",
            "/api/items/{name}": "one item",
            "/api/value": "?name=&age=default|neon|mega&potion=nopotion|ride|fly|fly_ride",
            "/api/types": "item types",
        },
    }


@app.get("/api/types")
def types():
    return sorted({i["type"] for i in snapshot()["items"]})


@app.get("/api/items")
def items(type: str | None = None, q: str | None = None):
    snap = snapshot()
    out = snap["items"]
    if type:
        out = [i for i in out if i["type"] == type]
    if q:
        q = q.lower()
        out = [i for i in out if q in i["name"].lower()]
    return {"count": len(out), "updated_at": snap["updated_at"], "items": out}


@app.get("/api/items/{name}")
def item(name: str):
    return find_item(name)


@app.get("/api/pets")
def pets(q: str | None = None):
    return items(type="pets", q=q)


@app.get("/api/pets/{name}")
def pet(name: str):
    return find_item(name, "pets")


@app.get("/api/value")
def value(
    name: str,
    age: str = Query("default", enum=list(AGES)),
    potion: str = Query("nopotion", enum=list(POTIONS)),
):
    i = find_item(name)
    v = i["values"][age][potion] if "values" in i else i["value"]
    return {"name": i["name"], "age": age, "potion": potion, "value": v}
