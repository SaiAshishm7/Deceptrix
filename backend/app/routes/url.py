
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.ml.url_model import predict_url

router = APIRouter(prefix="/api/url", tags=["URL Detection"])


class URLRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


@router.post("/analyze")
def analyze_url(request: URLRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    try:
        result = predict_url(url)
        result["url"] = url
        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="URL analysis failed"
        )
