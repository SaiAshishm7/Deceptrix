
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.engines.qr_engine import decode_qr
from backend.app.ml.url_model import predict_url

router = APIRouter(prefix="/api/qr", tags=["QR Detection"])

MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def analyze_payload(payload: str):
    value = payload.strip()

    if not value:
        return {
            "payload_type": "text",
            "message": "QR code contains empty text"
        }

    if value.lower().startswith("www."):
        value = "https://" + value

    parsed = urlparse(value)

    if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
        try:
            result = predict_url(value)

            return {
                "payload_type": "url",
                "decoded_url": value,
                "url_analysis": result
            }
        except Exception:
            return {
                "payload_type": "url",
                "decoded_url": value,
                "error": "URL analysis failed"
            }

    if parsed.scheme.lower() == "upi" and parsed.netloc.lower() == "pay":
        params = parse_qs(parsed.query)

        return {
            "payload_type": "upi_payment",
            "payment_details": {
                "payee_name": params.get("pn", [None])[0],
                "upi_id": params.get("pa", [None])[0],
                "amount": params.get("am", [None])[0],
                "currency": params.get("cu", [None])[0],
                "transaction_note": params.get("tn", [None])[0]
            },
            "security_notice": (
                "Payment details were decoded only. "
                "The recipient and payment request have not been verified. "
                "Do not pay unless you independently trust the recipient."
            )
        }

    return {
        "payload_type": "text",
        "decoded_text": value,
        "message": "QR code contains text rather than a supported URL or UPI payment payload"
    }


@router.post("/analyze")
async def analyze_qr(file: UploadFile = File(...)):
    allowed_types = {"image/png", "image/jpeg"}

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PNG and JPEG images are supported"
        )

    try:
        image_bytes = await file.read(MAX_UPLOAD_SIZE + 1)

        if len(image_bytes) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image size must not exceed 5 MB"
            )

        payload = decode_qr(image_bytes)
        analysis = analyze_payload(payload)

        return {
            "status": "success",
            "qr_decoded": True,
            **analysis
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="QR analysis failed"
        )
    finally:
        await file.close()
