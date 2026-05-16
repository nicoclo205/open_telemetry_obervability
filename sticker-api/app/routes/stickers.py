from fastapi import APIRouter, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.trace import StatusCode

from app.models.sticker import Sticker
from app.services.db_client import DbClient

router = APIRouter(prefix="/stickers", tags=["stickers"])
db = DbClient()

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter(
    "sticker_requests_total", description="Total sticker API requests"
)


@router.get("", response_model=list[Sticker])
async def list_stickers(pais: str = None, rareza: str = None):
    with tracer.start_as_current_span("sticker.list") as span:
        span.set_attribute("sticker.pais", pais or "")
        span.set_attribute("sticker.rareza", rareza or "")
        request_counter.add(1, {"endpoint": "list"})
        try:
            result = await db.get_all(pais, rareza)
            return result
        except Exception as e:
            span.set_status(StatusCode.ERROR)
            span.record_exception(e)
            raise


@router.get("/album/{numero_album}", response_model=list[Sticker])
async def get_stickers_by_album(numero_album: int):
    with tracer.start_as_current_span("sticker.album") as span:
        span.set_attribute("sticker.numero_album", numero_album)
        request_counter.add(1, {"endpoint": "album"})
        try:
            result = await db.get_by_album(numero_album)
            return result
        except Exception as e:
            span.set_status(StatusCode.ERROR)
            span.record_exception(e)
            raise


@router.get("/{id}", response_model=Sticker)
async def get_sticker(id: int):
    with tracer.start_as_current_span("sticker.get") as span:
        span.set_attribute("sticker.id", id)
        request_counter.add(1, {"endpoint": "get"})
        try:
            return await db.get_by_id(id)
        except Exception as exc:
            span.set_status(StatusCode.ERROR)
            span.record_exception(exc)
            if hasattr(exc, "response") and exc.response.status_code == 404:
                raise HTTPException(status_code=404)
            raise
