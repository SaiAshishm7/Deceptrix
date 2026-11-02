import qrcode
from pathlib import Path

output = Path("storage/uploads")
output.mkdir(parents=True, exist_ok=True)

samples = {
    "legitimate_url.png": "https://www.google.com",
    "suspicious_url.png": "https://paypal-secure-login.example.com/account/verify",
    "plain_text.png": "Hello from Deceptrix!",
    "upi_payment.png": "upi://pay?pa=demo@upi&pn=Demo%20Merchant&am=100&cu=INR"
}

for filename, payload in samples.items():
    image = qrcode.make(payload)
    image.save(output / filename)
    print(f"Generated: {output / filename}")