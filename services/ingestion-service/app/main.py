from fastapi import FastAPI

app = FastAPI(
    title="ingestion-service",
    description="DocuFlow AI ingestion-service",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {
        "service": "ingestion-service",
        "status": "healthy"
    }
