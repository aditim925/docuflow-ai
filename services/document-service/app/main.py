
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.documents import router as documents_router
from app.db.session import get_db

from contextlib import asynccontextmanager
from app.messaging.rabbitmq import rabbitmq_manager

#User id 35a8b110-403a-4ffb-aea6-9fc3bc51f242

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await rabbitmq_manager.connect()

    yield

    # Shutdown
    await rabbitmq_manager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(documents_router)



@app.get("/health")
async def health_check():
    return {"service": "document-service", "status": "healthy"}


@app.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "service": "document-service",
            "database": "connected",
            "status": "healthy",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc
