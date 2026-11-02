
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.engines.dns_engine import analyze_dns

router = APIRouter(
    prefix="/api/dns",
    tags=["DNS Analysis"]
)


class DNSRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


@router.post("/analyze")
def analyze_dns_endpoint(request: DNSRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    try:
        result = analyze_dns(url)
        result["url"] = url
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print(f"DNS analysis error: {error}")
        raise HTTPException(
            status_code=500,
            detail="DNS analysis failed"
        )
