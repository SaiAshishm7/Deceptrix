
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.engines.scan_engine import analyze_url_comprehensive

router = APIRouter(
    prefix="/api/scan",
    tags=["Comprehensive Scan"]
)


class ScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


@router.post("/analyze")
def comprehensive_scan(request: ScanRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    try:
        return analyze_url_comprehensive(url)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print(f"Comprehensive scan error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Comprehensive URL analysis failed"
        )
