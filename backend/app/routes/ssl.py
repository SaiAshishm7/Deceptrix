
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.engines.ssl_engine import analyze_ssl

router = APIRouter(
    prefix="/api/ssl",
    tags=["SSL/TLS Analysis"]
)


class SSLRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


@router.post("/analyze")
def analyze_ssl_endpoint(request: SSLRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    try:
        result = analyze_ssl(url)
        result["url"] = url
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print(f"SSL analysis error: {error}")
        raise HTTPException(
            status_code=500,
            detail="SSL analysis failed"
        )
