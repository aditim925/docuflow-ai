from fastapi import FastAPI

app = FastAPI(
    title="notification-service",
    description="DocuFlow AI notification-service",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {
        "service": "notification-service",
        "status": "healthy"
    }
