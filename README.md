# URL Shortener

Modern full-stack structure for a URL shortener app.

- `backend/` contains the Python API sources.
- `frontend/` contains the TypeScript React app sources.

> Installation files such as package manifests and Docker files are not included per request.
## Backend Usage

Run the backend API locally. The service supports optional Redis backing and environment configuration.

Prerequisites:
- Python 3.11+
- (optional) Redis server if you want persistent slug storage and TTL enforcement

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Environment variables (optional):
- `REDIS_URL` — Redis connection string (e.g. `redis://localhost:6379/0`). When set, slug storage and TTLs use Redis.
- `REDIS_PASSWORD` — Optional Redis password secret used to connect to protected Redis instances.
- `EXTERNAL_DOMAIN` — Public domain for short links (include scheme), e.g. `https://short.example`.
- `BASE_URL` — Fallback base URL used when `EXTERNAL_DOMAIN` is not set. Default: `http://localhost:8000`.
- `DEFAULT_URL_TTL` — Default TTL in seconds for short URLs when not specified in request. Default: no expiration.

Run the API (development):

```bash
# example with Redis
export REDIS_URL=redis://localhost:6379/0
export EXTERNAL_DOMAIN=https://short.example  # optional
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API endpoints:
- `GET /health` — health check
- `POST /api/v1/urls` — create short URL. JSON payload: `{ "target_url": "https://...", "slug": "optional-custom", "ttl": 600, "reuse_existing": false }` where `ttl` is seconds. If `ttl` is omitted, uses `DEFAULT_URL_TTL` if set.
- `GET /shrt/{slug}` — redirect to original URL (returns 404 if missing or expired)

Example `curl` to create a short URL:

```bash
curl -X POST http://localhost:8000/api/v1/urls \
	-H "Content-Type: application/json" \
	-d '{"target_url":"https://example.com","ttl":600}'
```

Notes:
- When `REDIS_URL` is set, the service uses atomic Redis `SET NX` to avoid slug collisions.
- If Redis is not configured the service falls back to a process-local in-memory store (ephemeral).
- **URL Deduplication**: By default, the same target URL always generates the same hash-based slug. This prevents duplicate short URLs in the database.
- **Short URL Loop Prevention**: The API rejects requests to shorten URLs that belong to the app's domain (determined by `EXTERNAL_DOMAIN` or `BASE_URL`), preventing redirect loops.
- **Hash-based Slugs**: The default slug is derived from the SHA256 hash of the target URL, ensuring deterministic generation. Custom slugs override this behavior.
