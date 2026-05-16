# Proyecto: Observabilidad Microservicios — Álbum Mundial
## Participante: Mao

> Antes de empezar, Claude Code pedirá identificarte. Escribe tu nombre cuando lo solicite.
> Este archivo es **tu mitad** del proyecto. Trabájalo con Claude Code de forma independiente.

---

## Contexto del proyecto

Arquitectura de 2 microservicios para consulta de stickers del álbum del Mundial, con observabilidad full-stack via OpenTelemetry + New Relic.

```
Cliente → sticker-api (REST público) → sticker-db-service (consulta SQL) → PostgreSQL
              |                                |
         OTel SDK                         OTel SDK
              \                              /
               → OTel Collector → New Relic
```

**Stack:**
- Python + FastAPI
- PostgreSQL
- OpenTelemetry Python SDK (automático + manual)
- Docker Compose
- New Relic OTLP endpoint

---

## Tu responsabilidad: `sticker-api` (API pública REST)

Este servicio recibe las peticiones del cliente y delega la consulta de datos al `sticker-db-service`.

---

## Grupo 1 — Scaffold del proyecto

**Agente:** `senior-implementer`

---

Identifícate al inicio: pregúntame mi nombre y confirma que soy Mao antes de proceder.

Crea la estructura base del proyecto `sticker-api` en Python + FastAPI con Docker:

```
sticker-api/
  app/
    main.py
    routes/
      stickers.py
    services/
      db_client.py       # cliente HTTP hacia sticker-db-service
    models/
      sticker.py
    telemetry/
      setup.py           # inicialización OTel SDK
  Dockerfile
  requirements.txt
```

Reglas:
- FastAPI con uvicorn
- Puerto 8000
- Variable de entorno `DB_SERVICE_URL` para apuntar a sticker-db-service
- Variable `OTEL_EXPORTER_OTLP_ENDPOINT` para el collector
- `requirements.txt` incluye: fastapi, uvicorn, httpx, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-exporter-otlp-proto-grpc
- Sin lógica de negocio aún, solo estructura y health check en GET /health

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 2 — Endpoints REST de stickers

**Agente:** `senior-implementer`

---

En `sticker-api`, implementa los siguientes endpoints en `routes/stickers.py`:

- `GET /stickers` — lista todos los stickers (con query params: `?pais=&rareza=`)
- `GET /stickers/{id}` — detalle de un sticker por ID
- `GET /stickers/album/{numero_album}` — todos los stickers de un álbum

Cada endpoint debe:
1. Recibir la petición
2. Llamar a `sticker-db-service` via HTTP usando `db_client.py` (usa `httpx.AsyncClient`)
3. Retornar la respuesta con el mismo `trace_id` propagado en headers (`traceparent`)

Modelos Pydantic en `models/sticker.py`:
```python
class Sticker(BaseModel):
    id: int
    nombre: str
    pais: str
    numero: int
    rareza: str  # "comun", "raro", "legendario"
    coleccionado: bool
```

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 3 — Instrumentación OTel (SDK manual + automático)

**Agente:** `senior-implementer`

---

En `sticker-api/app/telemetry/setup.py`, implementa la inicialización completa del SDK de OpenTelemetry:

```python
# Debe configurar:
# - TracerProvider con OTLPSpanExporter (gRPC)
# - MeterProvider con OTLPMetricExporter
# - LoggerProvider con OTLPLogExporter
# - Propagadores: TraceContext + Baggage
# - Auto-instrumentación: FastAPIInstrumentor, HTTPXClientInstrumentor
```

Luego en cada endpoint, agrega instrumentación manual:
- Span personalizado por operación: `sticker.list`, `sticker.get`, `sticker.album`
- Atributos en cada span: `sticker.id`, `sticker.pais`, `http.client.url`
- Métrica custom: contador `sticker_requests_total` con label `endpoint`
- En caso de error: `span.set_status(StatusCode.ERROR)` + `span.record_exception(e)`

El `trace_id` debe propagarse al llamar a `sticker-db-service` via header `traceparent` (W3C format). Usa `inject()` del propagador antes del request HTTP.

Correlación de logs: cada log debe incluir `trace_id` y `span_id` del span activo.

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 4 — Docker Compose completo (coordinado con Nico)

**Agente:** `senior-implementer`

---

> ⚠️ Este grupo lo trabajas junto con Nico. Él genera `docker-compose.yml` base desde su lado. Tú agregas el servicio `sticker-api`.

Crea el bloque de servicio para agregar al `docker-compose.yml` del proyecto raíz:

```yaml
sticker-api:
  build: ./sticker-api
  ports:
    - "8000:8000"
  environment:
    - DB_SERVICE_URL=http://sticker-db-service:8001
    - OTEL_SERVICE_NAME=sticker-api
    - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    - OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=dev
  depends_on:
    - sticker-db-service
    - otel-collector
  networks:
    - observabilidad-net
```

También crea `sticker-api/Dockerfile`:
- Base: `python:3.12-slim`
- Instala dependencias con pip
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 5 — Validación end-to-end

**Agente:** `qa-strategist`

---

Crea un script `scripts/test_trace.sh` que:

1. Haga `curl -X GET http://localhost:8000/stickers` y capture el `trace_id` del header de respuesta
2. Haga `curl -X GET http://localhost:8000/stickers/1`
3. Imprima los `trace_id` obtenidos
4. Verifique que el `otel-collector` está recibiendo datos: `curl http://localhost:8888/metrics`

Además, crea `scripts/load_test.py` con `httpx` para generar 50 requests seguidos a distintos endpoints y simular carga para ver métricas en New Relic.

**Checklist de entrega:**
- [ ] GET /stickers responde 200
- [ ] trace_id visible en logs de sticker-api Y sticker-db-service (mismo ID)
- [ ] En New Relic: trace completo con 2+ spans
- [ ] Métrica custom `sticker_requests_total` aparece en New Relic
- [ ] Tiempo de BD visible como span separado

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Resumen

- 5 grupos | 5 tareas
- Orden: Scaffold → Endpoints → OTel SDK → Docker → Validación
- Dependencia crítica: Grupo 4 requiere coordinación con Nico para unificar `docker-compose.yml`
- New Relic API Key va en `.env` (nunca en el repo): `NEW_RELIC_LICENSE_KEY`
