
import cv2
import numpy as np


MAX_IMAGE_SIZE = 5 * 1024 * 1024


def decode_qr(image_bytes: bytes):
    if not image_bytes:
        raise ValueError("Uploaded image is empty")

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ValueError("Image size must not exceed 5 MB")

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid or unsupported image. Upload a PNG or JPEG image.")

    height, width = image.shape[:2]

    if width > 4000 or height > 4000:
        raise ValueError("Image dimensions must not exceed 4000 x 4000 pixels")

    detector = cv2.QRCodeDetector()
    payload, points, _ = detector.detectAndDecode(image)

    if points is None or not payload:
        raise ValueError("No readable QR code found in the uploaded image")

    return payload
