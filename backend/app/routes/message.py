
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.ml.message_model import predict_message
from backend.app.ml.url_model import predict_url

router = APIRouter(prefix="/api/message", tags=["Message Detection"])


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


def extract_urls(message: str):
    pattern = r"(?:https?://|www\.)[^\s<>\"']+"
    matches = re.findall(pattern, message, flags=re.IGNORECASE)

    urls = []
    seen = set()

    for url in matches:
        url = url.rstrip(".,!?;:)]}\"'")

        if url.lower().startswith("www."):
            url = "https://" + url

        if url and url not in seen:
            urls.append(url)
            seen.add(url)

    return urls


@router.post("/analyze")
def analyze_message(request: MessageRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        message_result = predict_message(message)
        extracted_urls = extract_urls(message)

        url_results = []

        for url in extracted_urls:
            try:
                result = predict_url(url)
                result["url"] = url
                url_results.append(result)
            except Exception:
                url_results.append({
                    "url": url,
                    "error": "URL analysis failed"
                })

        return {
            "message_assessment": message_result["prediction"],
            "spam_probability": message_result["spam_probability"],
            "risk_score": message_result["risk_score"],
            "model": message_result["model"],
            "classification": message_result["classification"],
            "urls_found": len(extracted_urls),
            "extracted_urls": extracted_urls,
            "url_analysis": url_results
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Message analysis failed"
        )
