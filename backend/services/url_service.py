import os
import secrets
import time
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import Optional

from models.url_model import UrlModel
from schemas.url import CreateUrlRequest, UrlResponse

try:
    import redis
except Exception:  # pragma: no cover - import guard
    redis = None


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
EXTERNAL_DOMAIN = os.getenv("EXTERNAL_DOMAIN")
REDIS_URL = os.getenv("REDIS_URL")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
DEFAULT_URL_TTL = int(os.getenv("DEFAULT_URL_TTL", "0")) or None


class UrlService:
    def __init__(self) -> None:
        # in-memory store maps slug -> (UrlModel, expires_at_timestamp)
        self._store: dict[str, tuple[UrlModel, Optional[float]]] = {}
        self._redis = None
        if REDIS_URL and redis is not None:
            connection_kwargs = {"decode_responses": True}
            if REDIS_PASSWORD:
                connection_kwargs["password"] = REDIS_PASSWORD
            self._redis = redis.Redis.from_url(REDIS_URL, **connection_kwargs)

    def _short_base(self) -> str:
        base = EXTERNAL_DOMAIN or BASE_URL
        if not base.endswith("/"):
            base = base + "/"
        return base

    def _is_short_url(self, url: str) -> bool:
        """Check if the given URL is a short URL belonging to this app."""
        try:
            parsed = urlparse(url)
            base = self._short_base().rstrip("/")
            base_parsed = urlparse(base)
            return parsed.netloc == base_parsed.netloc
        except Exception:
            return False

    def _hash_url(self, url: str) -> str:
        """Create a deterministic slug from URL hash."""
        url_hash = hashlib.sha256(url.encode()).digest()
        # Create hash-based slug: take first 8 chars of base64-encoded hash
        import base64
        hash_slug = base64.urlsafe_b64encode(url_hash[:6]).decode().rstrip("=")[:8]
        return hash_slug


    def create_short_url(self, payload: CreateUrlRequest) -> UrlResponse:
        requested_slug = payload.slug
        ttl = payload.ttl if payload.ttl is not None else DEFAULT_URL_TTL
        target_url_str = str(payload.target_url)

        # Validate: prevent shortening of short URLs (avoid redirect loops)
        if self._is_short_url(target_url_str):
            raise ValueError("cannot_shorten_short_url")

        # helper to compute expires_at
        expires_at_dt = None
        if ttl is not None:
            expires_at_dt = datetime.utcnow() + timedelta(seconds=ttl)

        # If user supplied a custom slug, validate and use it
        if requested_slug:
            if self._redis:
                key = f"url:{requested_slug}"
                existing = self._redis.get(key)
                if existing and existing != target_url_str:
                    raise ValueError("slug_taken")
                ok = self._redis.set(key, target_url_str, ex=ttl, nx=True)
                if not ok:
                    raise ValueError("slug_taken")
                short_url = urljoin(self._short_base(), f"shrt/{requested_slug}")
                return UrlResponse(slug=requested_slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)
            else:
                existing = self._store.get(requested_slug)
                if existing:
                    _, expires_ts = existing
                    if not expires_ts or expires_ts > time.time():
                        model, _ = existing
                        if str(model.target_url) != target_url_str:
                            raise ValueError("slug_taken")
                        # Same URL with same slug - return existing
                        short_url = urljoin(self._short_base(), f"shrt/{requested_slug}")
                        return UrlResponse(slug=requested_slug, short_url=short_url, target_url=payload.target_url, expires_at=model.expires_at)
                expires_ts = time.time() + ttl if ttl is not None else None
                model = UrlModel(slug=requested_slug, target_url=payload.target_url, expires_at=expires_at_dt)
                self._store[requested_slug] = (model, expires_ts)
                short_url = urljoin(self._short_base(), f"shrt/{requested_slug}")
                return UrlResponse(slug=requested_slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)

        # Try hash-based slug first (deterministic deduplication)
        hash_slug = self._hash_url(target_url_str)
        
        if self._redis:
            key = f"url:{hash_slug}"
            existing = self._redis.get(key)
            if existing and existing == target_url_str:
                # Hash-slug exists and maps to same URL - return it (deduplication)
                short_url = urljoin(self._short_base(), f"shrt/{hash_slug}")
                return UrlResponse(slug=hash_slug, short_url=short_url, target_url=payload.target_url, expires_at=None)
            
            if not existing:
                # Hash-slug is free - use it
                ok = self._redis.set(key, target_url_str, ex=ttl, nx=True)
                if ok:
                    short_url = urljoin(self._short_base(), f"shrt/{hash_slug}")
                    return UrlResponse(slug=hash_slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)

            # Hash-slug taken by different URL - fall back to random slug
            for _ in range(10):
                slug = self._generate_slug()
                key = f"url:{slug}"
                ok = self._redis.set(key, target_url_str, ex=ttl, nx=True)
                if ok:
                    short_url = urljoin(self._short_base(), f"shrt/{slug}")
                    return UrlResponse(slug=slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)
            raise RuntimeError("unable_to_generate_unique_slug")
        else:
            # In-memory fallback
            existing_hash = self._store.get(hash_slug)
            if existing_hash:
                model, expires_ts = existing_hash
                if not expires_ts or expires_ts > time.time():
                    if str(model.target_url) == target_url_str:
                        # Same URL - return existing
                        short_url = urljoin(self._short_base(), f"shrt/{hash_slug}")
                        return UrlResponse(slug=hash_slug, short_url=short_url, target_url=payload.target_url, expires_at=model.expires_at)
                    # Different URL - fall through to random slug
                else:
                    # Expired - reuse hash-slug
                    expires_ts = time.time() + ttl if ttl is not None else None
                    model = UrlModel(slug=hash_slug, target_url=payload.target_url, expires_at=expires_at_dt)
                    self._store[hash_slug] = (model, expires_ts)
                    short_url = urljoin(self._short_base(), f"shrt/{hash_slug}")
                    return UrlResponse(slug=hash_slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)
            else:
                # Hash-slug is free - use it
                expires_ts = time.time() + ttl if ttl is not None else None
                model = UrlModel(slug=hash_slug, target_url=payload.target_url, expires_at=expires_at_dt)
                self._store[hash_slug] = (model, expires_ts)
                short_url = urljoin(self._short_base(), f"shrt/{hash_slug}")
                return UrlResponse(slug=hash_slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)

            # Fall back to random slug generation
            for _ in range(10):
                slug = self._generate_slug()
                existing = self._store.get(slug)
                if existing:
                    _, expires_ts = existing
                    if not expires_ts or expires_ts <= time.time():
                        # expired - reuse
                        pass
                    else:
                        continue
                expires_ts = time.time() + ttl if ttl is not None else None
                model = UrlModel(slug=slug, target_url=payload.target_url, expires_at=expires_at_dt)
                self._store[slug] = (model, expires_ts)
                short_url = urljoin(self._short_base(), f"shrt/{slug}")
                return UrlResponse(slug=slug, short_url=short_url, target_url=payload.target_url, expires_at=expires_at_dt)

            raise RuntimeError("unable_to_generate_unique_slug")

    def get_original_url(self, slug: str) -> str | None:
        if self._redis:
            key = f"url:{slug}"
            value = self._redis.get(key)
            return value if value else None

        record = self._store.get(slug)
        if not record:
            return None
        model, expires_ts = record
        if expires_ts and expires_ts <= time.time():
            # expired - remove
            del self._store[slug]
            return None
        return str(model.target_url)

    def get_url_record(self, slug: str) -> UrlResponse | None:
        if self._redis:
            value = self._redis.get(f"url:{slug}")
            if not value:
                return None
            return UrlResponse(slug=slug, short_url=urljoin(self._short_base(), f"shrt/{slug}"), target_url=value, expires_at=None)

        record = self._store.get(slug)
        if not record:
            return None
        model, expires_ts = record
        if expires_ts and expires_ts <= time.time():
            del self._store[slug]
            return None
        return UrlResponse(slug=model.slug, short_url=urljoin(self._short_base(), model.slug), target_url=model.target_url, expires_at=model.expires_at)

    def _generate_slug(self) -> str:
        return secrets.token_urlsafe(5)

    def _find_existing_slug(self, target_url: str) -> Optional[str]:
        """Find an existing non-expired slug for the given target URL."""
        if self._redis:
            # Redis: would need a reverse index, skip for now
            return None

        # In-memory: iterate to find match
        for slug, (model, expires_ts) in self._store.items():
            # Check if not expired
            if expires_ts and expires_ts <= time.time():
                continue
            if str(model.target_url) == target_url:
                return slug
        return None


service = UrlService()
