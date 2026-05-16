from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.routes import stickers
from app.telemetry.setup import setup_telemetry

setup_telemetry()

try:
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    LoggingInstrumentor().instrument(set_logging_format=True)
except ImportError:
    pass

app = FastAPI(title="sticker-api")

app.include_router(stickers.router)

FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
