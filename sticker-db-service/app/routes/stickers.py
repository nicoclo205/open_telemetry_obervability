import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from opentelemetry import metrics, propagate, trace

from app.db import queries

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stickers", tags=["stickers"])

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

query_duration_histogram = meter.create_histogram(
    name="db_query_duration_ms",
    description="Duración de queries a PostgreSQL en milisegundos",
    unit="ms",
)
db_errors_counter = meter.create_counter(
    name="db_errors_total",
    description="Total de errores en queries a la base de datos",
)


@router.get("")
async def list_stickers(
    request: Request,
    pais: Optional[str] = Query(None),
    rareza: Optional[str] = Query(None),
):
    # Extraemos el contexto del header traceparent para propagar el mismo trace_id
    ctx = propagate.extract(dict(request.headers))
    with tracer.start_as_current_span("db.query.list", context=ctx) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")
        if pais:
            span.set_attribute("db.query.filter.pais", pais)
        if rareza:
            span.set_attribute("db.query.filter.rareza", rareza)
        try:
            rows, duration_ms = await queries.get_all_stickers(pais=pais, rareza=rareza)
            span.set_attribute("db.rows_returned", len(rows))
            span.set_attribute("db.query.duration_ms", round(duration_ms, 3))
            query_duration_histogram.record(duration_ms, {"operation": "list"})
            return rows
        except Exception as exc:
            db_errors_counter.add(1, {"error_type": type(exc).__name__})
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            logger.exception("Error in list_stickers")
            raise HTTPException(status_code=500, detail="Error consultando stickers")


# IMPORTANTE: la ruta /album/{numero_album} debe definirse ANTES de /{id}
# para que FastAPI no interprete la palabra "album" como un entero de id.
@router.get("/album/{numero_album}")
async def stickers_by_album(numero_album: int, request: Request):
    ctx = propagate.extract(dict(request.headers))
    with tracer.start_as_current_span("db.query.album", context=ctx) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.query.numero_album", numero_album)
        try:
            rows, duration_ms = await queries.get_stickers_by_album(numero_album)
            span.set_attribute("db.rows_returned", len(rows))
            span.set_attribute("db.query.duration_ms", round(duration_ms, 3))
            query_duration_histogram.record(duration_ms, {"operation": "album"})
            return rows
        except Exception as exc:
            db_errors_counter.add(1, {"error_type": type(exc).__name__})
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            logger.exception("Error in stickers_by_album")
            raise HTTPException(status_code=500, detail="Error consultando álbum")


@router.get("/{sticker_id}")
async def get_sticker(sticker_id: int, request: Request):
    ctx = propagate.extract(dict(request.headers))
    with tracer.start_as_current_span("db.query.get", context=ctx) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.query.sticker_id", sticker_id)
        try:
            row, duration_ms = await queries.get_sticker_by_id(sticker_id)
            span.set_attribute("db.query.duration_ms", round(duration_ms, 3))
            query_duration_histogram.record(duration_ms, {"operation": "get"})
            if row is None:
                raise HTTPException(status_code=404, detail=f"Sticker {sticker_id} no encontrado")
            span.set_attribute("db.rows_returned", 1)
            return row
        except HTTPException:
            raise
        except Exception as exc:
            db_errors_counter.add(1, {"error_type": type(exc).__name__})
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            logger.exception("Error in get_sticker")
            raise HTTPException(status_code=500, detail="Error consultando sticker")
