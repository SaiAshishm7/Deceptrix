
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.qr_engine import decode_qr

folder = ROOT_DIR / "storage" / "uploads"

for image_path in sorted(folder.glob("*.png")):
    print(f"\nFile: {image_path.name}")

    try:
        payload = decode_qr(image_path.read_bytes())
        print(f"Decoded: {payload}")
    except ValueError as error:
        print(f"Error: {error}")
