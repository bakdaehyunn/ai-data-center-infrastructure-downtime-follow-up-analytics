from fastapi import FastAPI

from app.api.routes import router as api_router
from app.settings import Settings


settings = Settings()

app = FastAPI(
    title="Critical Procurement Bottleneck Analytics API",
    version="0.1.0",
)
app.include_router(api_router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
    }
