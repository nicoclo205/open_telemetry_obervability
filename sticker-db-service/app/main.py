import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.telemetry.setup import setup_telemetry
from app.db.connection import init_pool, close_pool
from app.routes.stickers import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(app)
    await init_pool()
    logger.info("sticker-db-service started")
    yield
    await close_pool()
    logger.info("sticker-db-service stopped")


app = FastAPI(title="sticker-db-service", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sticker-db-service"}
