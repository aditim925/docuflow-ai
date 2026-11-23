from fastapi import FastAPI

app = FastAPI(
    title="chat-service",
    description="DocuFlow AI chat-service",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {
        "service": "chat-service",
        "status": "healthy"
    }
