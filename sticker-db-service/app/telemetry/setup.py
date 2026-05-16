import logging
import os
from typing import Optional

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textformat_propagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def setup_telemetry(app: Optional[FastAPI] = None) -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    service_name = os.environ.get("OTEL_SERVICE_NAME", "sticker-db-service")

    # El Resource identifica este servicio en New Relic (aparece como nombre de servicio)
    resource = Resource.create({SERVICE_NAME: service_name})

    # ── Trazas ──────────────────────────────────────────────────────────────
    # TracerProvider es el objeto raíz que crea y gestiona los Tracers.
    # BatchSpanProcessor acumula spans en buffer y los envía al Collector en lotes
    # para no hacer una llamada gRPC por cada span individual.
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint, insecure=True)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # ── Métricas ─────────────────────────────────────────────────────────────
    # PeriodicExportingMetricReader recolecta y exporta métricas cada 5 segundos.
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=5_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # ── Logs ─────────────────────────────────────────────────────────────────
    # LoggerProvider gestiona los loggers OTel.  LoggingHandler es un handler
    # estándar de Python logging que convierte cada log entry en un OTel LogRecord,
    # y añade automáticamente trace_id y span_id al contexto del log.
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=endpoint, insecure=True)
        )
    )
    set_logger_provider(logger_provider)

    otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.addHandler(otel_handler)
    root_logger.setLevel(logging.INFO)

    # ── Propagadores ─────────────────────────────────────────────────────────
    # TraceContext: propaga trace_id y span_id vía header "traceparent" (W3C estándar).
    # W3CBaggage: propaga metadatos de negocio vía header "baggage".
    # CompositePropagator aplica ambos propagadores en orden.
    set_global_textformat_propagator(
        CompositePropagator([
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ])
    )

    # ── Auto-instrumentación ─────────────────────────────────────────────────
    # AsyncPGInstrumentor envuelve automáticamente cada query de asyncpg con un span.
    AsyncPGInstrumentor().instrument()

    # FastAPIInstrumentor crea un span por cada request HTTP y extrae el
    # traceparent del header entrante para conectar con el trace upstream.
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    else:
        FastAPIInstrumentor().instrument()
