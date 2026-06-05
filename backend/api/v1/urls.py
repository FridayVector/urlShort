from fastapi import APIRouter, HTTPException
from schemas.url import CreateUrlRequest, UrlResponse
from services import service

router = APIRouter()


@router.post("/urls", response_model=UrlResponse)
def create_url(payload: CreateUrlRequest) -> UrlResponse:
    try:
        return service.create_short_url(payload)
    except ValueError as exc:
        error_msg = str(exc)
        if error_msg == "slug_taken":
            raise HTTPException(status_code=409, detail="Requested slug is already taken")
        elif error_msg == "cannot_shorten_short_url":
            raise HTTPException(status_code=400, detail="Cannot create short URL of a short URL (redirect loop prevention)")
        raise HTTPException(status_code=400, detail=error_msg)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/urls/{slug}")
def get_url(slug: str) -> UrlResponse:
    record = service.get_url_record(slug)
    if not record:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return record
