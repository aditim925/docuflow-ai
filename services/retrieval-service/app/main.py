from fastapi import FastAPI

app = FastAPI(
    title="retrieval-service",
    description="DocuFlow AI retrieval-service",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {
        "service": "retrieval-service",
        "status": "healthy"
    }
