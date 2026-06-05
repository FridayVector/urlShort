from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from api.v1.urls import router as urls_router
from services import service

app = FastAPI(title="URL Shortener API", version="0.1.0")

app.include_router(urls_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/shrt/{slug}")
def resolve_short_url(slug: str):
    original_url = service.get_original_url(slug)
    if not original_url:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=original_url)
