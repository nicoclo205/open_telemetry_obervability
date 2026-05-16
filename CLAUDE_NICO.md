# Proyecto: Observabilidad Microservicios — Álbum Mundial
## Participante: Nico

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

## Tu responsabilidad: `sticker-db-service` + OTel Collector + Docker Compose raíz

Este servicio recibe peticiones de `sticker-api`, consulta la base de datos PostgreSQL y retorna los resultados. También eres responsable de la infraestructura de observabilidad (collector, base de datos, compose raíz).

---

## Grupo 1 — Scaffold del proyecto

**Agente:** `senior-implementer`

---

Identifícate al inicio: pregúntame mi nombre y confirma que soy Nico antes de proceder.

Crea la estructura base del proyecto `sticker-db-service` en Python + FastAPI con Docker:

```
sticker-db-service/
  app/
    main.py
    routes/
      stickers.py
    db/
      connection.py     # pool de conexiones asyncpg
      queries.py        # queries SQL
    models/
      sticker.py
    telemetry/
      setup.py          # inicialización OTel SDK
  Dockerfile
  requirements.txt
  init.sql              # schema + datos de ejemplo
```

Reglas:
- FastAPI con uvicorn
- Puerto 8001 (interno, no expuesto al host)
- Variables de entorno: `DATABASE_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- `requirements.txt` incluye: fastapi, uvicorn, asyncpg, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-asyncpg, opentelemetry-exporter-otlp-proto-grpc
- Sin lógica aún, solo estructura y GET /health

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 2 — Base de datos y queries

**Agente:** `senior-implementer`

---

En `sticker-db-service`, implementa:

**`init.sql`** — Schema PostgreSQL:
```sql
CREATE TABLE stickers (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    numero INTEGER NOT NULL,
    rareza VARCHAR(20) CHECK (rareza IN ('comun', 'raro', 'legendario')),
    coleccionado BOOLEAN DEFAULT FALSE,
    numero_album INTEGER NOT NULL
);
-- Insertar al menos 30 stickers de ejemplo de distintos países y álbumes
```

**`db/connection.py`** — Pool asyncpg con context manager.

**`db/queries.py`** — Funciones async:
- `get_all_stickers(pais=None, rareza=None)` 
- `get_sticker_by_id(id)`
- `get_stickers_by_album(numero_album)`

Cada función debe medir su tiempo de ejecución para exponerlo como span OTel.

**`routes/stickers.py`** — Endpoints:
- `GET /stickers` — con filtros opcionales `?pais=&rareza=`
- `GET /stickers/{id}`
- `GET /stickers/album/{numero_album}`

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 3 — Instrumentación OTel (SDK manual + automático)

**Agente:** `senior-implementer`

---

En `sticker-db-service/app/telemetry/setup.py`, implementa la inicialización completa del SDK:

```python
# Debe configurar:
# - TracerProvider con OTLPSpanExporter (gRPC)
# - MeterProvider con OTLPMetricExporter
# - LoggerProvider con OTLPLogExporter
# - Propagadores: TraceContext + Baggage
# - Auto-instrumentación: FastAPIInstrumentor, AsyncPGInstrumentor
```

Instrumentación manual en queries y endpoints:
- Span por query SQL: `db.query.list`, `db.query.get`, `db.query.album`
- Atributos: `db.system=postgresql`, `db.operation`, `db.rows_returned`
- **Span de latencia de BD**: medir tiempo exacto de cada query como atributo `db.query.duration_ms`
- Métricas custom:
  - Histograma `db_query_duration_ms` por operación
  - Contador `db_errors_total` por tipo de error
- Propagación de contexto: extraer `traceparent` del header entrante con `extract()` y asignarlo como contexto padre del span — esto garantiza mismo `trace_id` end-to-end

Correlación de logs: incluir `trace_id` y `span_id` en cada entrada de log.

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 4 — OTel Collector + Docker Compose raíz

**Agente:** `senior-implementer`

---

Crea la infraestructura completa en el directorio raíz del proyecto:

**`otel-collector/collector-config.yaml`:**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 256

exporters:
  otlp/newrelic:
    endpoint: otlp.nr-data.net:4317
    headers:
      api-key: ${NEW_RELIC_LICENSE_KEY}
  logging:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/newrelic, logging]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/newrelic, logging]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/newrelic, logging]
```

**`docker-compose.yml`** raíz con todos los servicios:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: stickers_db
      POSTGRES_USER: stickers_user
      POSTGRES_PASSWORD: stickers_pass
    volumes:
      - ./sticker-db-service/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks: [observabilidad-net]

  sticker-db-service:
    build: ./sticker-db-service
    environment:
      - DATABASE_URL=postgresql://stickers_user:stickers_pass@postgres:5432/stickers_db
      - OTEL_SERVICE_NAME=sticker-db-service
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=dev
    depends_on: [postgres, otel-collector]
    networks: [observabilidad-net]

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel/collector-config.yaml"]
    volumes:
      - ./otel-collector/collector-config.yaml:/etc/otel/collector-config.yaml
    ports:
      - "4317:4317"
      - "4318:4318"
      - "8888:8888"
    env_file: .env
    networks: [observabilidad-net]

  # sticker-api se agrega desde el lado de Mao

networks:
  observabilidad-net:
    driver: bridge
```

También crea `.env.example`:
```
NEW_RELIC_LICENSE_KEY=tu_api_key_aqui
```

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Grupo 5 — Validación y checklist de entrega

**Agente:** `qa-strategist`

---

Verifica que el stack levanta correctamente:

1. `docker compose up --build` — todos los servicios deben quedar healthy
2. Prueba directa al db-service: `curl http://localhost:8001/health` (solo desde dentro de la red Docker)
3. Verifica logs del collector: `docker logs otel-collector` — debe mostrar spans recibidos
4. Confirma en New Relic:
   - Service map muestra `sticker-api` → `sticker-db-service`
   - Existe al menos 1 trace completo con `trace_id` compartido entre ambos servicios
   - Span de latencia de BD visible con `db.query.duration_ms`
   - Métrica custom `db_query_duration_ms` visible en New Relic

**Checklist de entrega:**
- [ ] `docker compose up` levanta sin errores
- [ ] PostgreSQL inicializado con datos de ejemplo
- [ ] OTel Collector recibiendo datos (logs muestran spans)
- [ ] New Relic recibe trazas de ambos servicios
- [ ] `trace_id` es el mismo en sticker-api y sticker-db-service
- [ ] Span de latencia de BD visible
- [ ] Métrica custom del histograma aparece en New Relic
- [ ] Dashboard de New Relic responde: ¿qué servicio tardó más?, ¿cuántos req/s?

**Preguntas que debe poder responder el sistema:**
- ¿Dónde inició el request? → primer span en sticker-api
- ¿Cuál servicio tardó más? → comparar duración de spans
- ¿Qué operación generó latencia? → atributo `db.query.duration_ms`
- ¿Cuántos requests/segundo? → métrica `sticker_requests_total`

> 💡 Después de completar este grupo, ejecuta `/clear` antes de continuar con el siguiente.

---

## Resumen

- 5 grupos | 5 tareas
- Orden: Scaffold → BD + Queries → OTel SDK → Collector + Compose → Validación
- Dependencia crítica: Grupo 4 debe compartirse con Mao para que agregue `sticker-api` al compose
- `.env` con `NEW_RELIC_LICENSE_KEY` nunca va al repo — agrega `.env` al `.gitignore`
