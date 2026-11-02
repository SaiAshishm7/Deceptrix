
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.message import router as message_router
from backend.app.routes.url import router as url_router
from backend.app.routes.qr import router as qr_router

app = FastAPI(
    title="Deceptrix API",
    description="AI-powered phishing and fraudulent URL detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(url_router)
app.include_router(message_router)
app.include_router(qr_router)

@app.get("/")
def root():
    return {
        "project": "Deceptrix",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
