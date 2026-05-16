# Observabilidad en Microservicios

Plataforma integral de observabilidad para una arquitectura de microservicios con trazas distribuidas, métricas en tiempo real y logs estructurados. Implementa OpenTelemetry como SDK estándar de instrumentación y New Relic como backend de observabilidad.

## Objetivo del Proyecto

Demostrar cómo instrumentar una arquitectura de microservicios de manera integral utilizando OpenTelemetry (OTEL), propagando contexto distribuido entre servicios y centralizando toda la telemetría en una plataforma de observabilidad (New Relic). El proyecto sirve como referencia educativa para entender cómo operacionalizar observabilidad en producción.

## Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                       Cliente / Load Test                         │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                    HTTP/REST (puerto 8000)
                         │
        ┌────────────────▼───────────────────┐
        │     sticker-api (FastAPI)          │
        │     - Gateway de entrada           │
        │     - Expone 3 endpoints GET       │
        │     - Orquesta requests a db-svc   │
        │     - Traces: propagación W3C      │
        └─────┬──────────────────────────────┘
              │
              │ HTTP gRPC OTLP        HTTP/REST (puerto 8001)
              │ (traces, metrics,     │
              │  logs)                │
        ┌─────▼──────────────────┬───▼───────────────────────────┐
        │ otel-collector         │ sticker-db-service (FastAPI)  │
        │ (OpenTelemetry)        │ - Microservicio de acceso BD  │
        │ - Recibe OTLP gRPC     │ - Instrumentación AsyncPG     │
        │ - Procesa telemetría   │ - Span customizados           │
        │ - Exporta a New Relic  │ - Contexto distribuido        │
        │   + output debug local │                               │
        └─────┬──────────────────┴───┬───────────────────────────┘
              │                      │
              │ gRPC otlp.nr-data   │ PostgreSQL asyncpg (5432)
              │     .net:4317        │
              │                      │
        ┌─────▼────────────────┐ ┌──▼────────────────────────────┐
        │  New Relic           │ │ PostgreSQL 16                  │
        │  (APM + Tracing)     │ │ - stickers_db                  │
        │  - Dashboard         │ │ - Schema: stickers, álbum      │
        │  - Error Tracking    │ │ - Connection pooling asyncpg   │
        │  - Log Management    │ │                                │
        └──────────────────────┘ └────────────────────────────────┘
```

## Stack Tecnológico

### Lenguaje y Framework
- **Python 3.11+** con **FastAPI** para ambos microservicios
- **Uvicorn** como servidor ASGI

### Observabilidad
- **OpenTelemetry SDK (v1.24.0+)**: Instrumentación de trazas, métricas y logs
  - FastAPI Instrumentor: captura automatización de requests HTTP
  - HTTPX Instrumentor: propaga contexto en HTTP outbound
  - AsyncPG Instrumentor: traza queries de base de datos
  - Logging Instrumentor: inyecta trace_id y span_id en logs
- **OTLP/gRPC exporter**: comunica con OpenTelemetry Collector
- **OpenTelemetry Collector Contrib**: receptor y procesador intermediario
- **New Relic**: backend de observabilidad (APM, Distributed Tracing, Logs)

### Base de Datos
- **PostgreSQL 16 Alpine**: almacenamiento persistente de stickers
- **asyncpg**: driver async Python para PostgreSQL
- Connection pooling integrado para concurrencia

### Infraestructura
- **Docker Compose** (desarrollo local): orquestación de 4 servicios en red aislada
- **Kubernetes (AKS - Azure Kubernetes Service)**: despliegue en producción
  - Namespace `observabilidad`
  - ClusterIP Services
  - Ingress nginx + IP pública
  - PersistentVolumeClaim (Azure managed-csi)
  - ConfigMaps y Secrets para configuración

## Decisiones Técnicas Clave

### 1. Propagación de Contexto Distribuido (W3C TraceContext + Baggage)
Se implementó propagación de contexto W3C estándar entre sticker-api y sticker-db-service via headers HTTP (`traceparent` y `baggage`). Esto permite que cada request genere una cadena de spans conectados end-to-end, visible en New Relic como una transacción unificada.

**Rationale**: W3C TraceContext es el estándar de la industria, agnóstico de vendor, garantizando portabilidad futura.

### 2. OpenTelemetry Collector como Gateway
El collector actúa como proxy intermediario (patrón sidecar/gateway), recibiendo telemetría en gRPC (puerto 4317) de ambos servicios y reenviando a New Relic. Incluye procesamiento local de batch y límites de memoria.

**Rationale**: Desacopla servicios del backend. Permite filtrado, muestreo o enriquecimiento de telemetría sin cambiar código de servicios.

### 3. Auto-Instrumentación vs Instrumentación Manual
Se usa auto-instrumentación donde es posible (FastAPI, AsyncPG, HTTP calls) pero con spans customizados manuales en las rutas críticas para capturar lógica de negocio específica.

**Rationale**: Balance entre cobertura automática y contexto semántico. Los spans manuales documentan decisiones de negocio (ej: "lista filtrada por país").

### 4. Logging Estructurado con Correlación
Los logs se exportan vía OTLP con trace_id y span_id inyectados automáticamente por el LoggingInstrumentor, permitiendo correlación perfecta en New Relic.

**Rationale**: Conecta logs con trazas distribuidas, eliminando la necesidad de buscar logs por timestamp o mensaje.

### 5. PostgreSQL en Kubernetes con PVC
Se usa un PersistentVolumeClaim en Kubernetes para PostgreSQL con PGDATA configurada en subdirectorio (`/var/lib/postgresql/data/pgdata`). Esto evita conflictos con directorios del CSI driver de Azure.

**Rationale**: Azure managed-csi crea `lost+found` en la raíz del volumen; mover PGDATA evita inicialización fallida.

## Cómo Ejecutar en Local (Docker Compose)

### Requisitos
- Docker y Docker Compose instalados
- Token/License Key de New Relic (opcional para desarrollo)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <repo-url>
   cd observabilidad-microservicios
   ```

2. **Configurar variables de entorno**
   Crear archivo `.env` en la raíz con (opcional):
   ```env
   NEW_RELIC_LICENSE_KEY=your_license_key_here
   ```
   Si no se proporciona, el collector exportará solo a debug (salida local).

3. **Levantar servicios con Docker Compose**
   ```bash
   docker-compose up -d
   ```

   Esto inicia:
   - PostgreSQL (puerto 5432 interno, schema inicializado automáticamente)
   - OpenTelemetry Collector (puertos 4317 gRPC, 4318 HTTP, 8888 metrics)
   - sticker-db-service (puerto 8001 interno, instrumentado con asyncpg)
   - sticker-api (puerto 8000 local, gateway instrumentado con FastAPI + HTTPX)

4. **Verificar salud de servicios**
   ```bash
   curl http://localhost:8000/health
   ```
   Respuesta esperada:
   ```json
   {"status": "ok"}
   ```

5. **Detener servicios**
   ```bash
   docker-compose down
   ```

### Verificación Local
Los logs del collector (stdout) mostrarán spans, métricas y logs procesados. Ver con:
```bash
docker-compose logs -f otel-collector
```

Buscar líneas como:
```
Span #0
	Trace ID   : ...
	Parent ID  : ...
	ID         : ...
	Name       : sticker.list
	...
```

## Cómo Desplegar en Kubernetes (AKS)

### Requisitos Previos
- Cluster AKS creado y configurado
- `kubectl` conectado al cluster
- Acceso a Azure Container Registry (ACR) o Docker Hub
- New Relic License Key en secreto de Kubernetes

### Pasos

1. **Construir y pushear imágenes**
   ```bash
   # Para sticker-api
   docker build -t <registry>/sticker-api:latest ./sticker-api
   docker push <registry>/sticker-api:latest

   # Para sticker-db-service
   docker build -t <registry>/sticker-db-service:latest ./sticker-db-service
   ```

2. **Crear namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

3. **Crear Secret con credenciales**
   ```bash
   kubectl create secret generic newrelic-secret \
     --from-literal=NEW_RELIC_LICENSE_KEY=<your-key> \
     -n observabilidad
   ```

4. **Actualizar referencias de imagen en deployments**
   Editar `k8s/deployments/sticker-api.yaml` y `sticker-db-service.yaml` para usar la imagen correcta:
   ```yaml
   spec:
     containers:
       - image: <registry>/sticker-api:latest
   ```

5. **Aplicar manifests en orden**
   ```bash
   # Volúmenes y configuración
   kubectl apply -f k8s/pvc/postgres.yaml
   kubectl apply -f k8s/configmaps/

   # Servicios
   kubectl apply -f k8s/services/

   # Deployments
   kubectl apply -f k8s/deployments/

   # Ingress
   kubectl apply -f k8s/ingress/sticker-api.yaml
   ```

6. **Verificar despliegue**
   ```bash
   kubectl get pods -n observabilidad
   kubectl get svc -n observabilidad
   kubectl get ingress -n observabilidad
   ```

### Acceso en Kubernetes
Una vez desplegado, el Ingress expone la API en:
```
http://sticker-api.local
```

Agregar a `/etc/hosts` (Linux/Mac) o `hosts` (Windows):
```
20.185.8.196 sticker-api.local
```

Donde `20.185.8.196` es la IP pública del Ingress (ajustar según tu despliegue).

### Escalar Deployments
```bash
kubectl scale deployment sticker-api --replicas=3 -n observabilidad
kubectl scale deployment sticker-db-service --replicas=2 -n observabilidad
```

## API REST - Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **Kubernetes**: `http://sticker-api.local` (con Ingress)

### Health Check
```bash
curl http://localhost:8000/health
```
**Respuesta** (200):
```json
{"status": "ok"}
```

### Listar Stickers
```bash
curl "http://localhost:8000/stickers"
```

Con filtros:
```bash
curl "http://localhost:8000/stickers?pais=Argentina&rareza=legendario"
```

**Parámetros**:
- `pais` (query, opcional): Filtrar por país (ej: "Argentina", "Brasil")
- `rareza` (query, opcional): Filtrar por rareza (ej: "legendario", "raro", "normal")

**Respuesta** (200):
```json
[
  {
    "id": 1,
    "nombre": "Messi",
    "pais": "Argentina",
    "rareza": "legendario",
    "numero_album": 1,
    "coleccionado": true
  },
  ...
]
```

### Obtener Sticker por ID
```bash
curl http://localhost:8000/stickers/1
```

**Parámetros**:
- `id` (path, requerido): ID único del sticker

**Respuesta** (200):
```json
{
  "id": 1,
  "nombre": "Messi",
  "pais": "Argentina",
  "rareza": "legendario",
  "numero_album": 1,
  "coleccionado": true
}
```

**Error** (404):
```json
{"detail": "Not Found"}
```

### Listar Stickers por Número de Álbum
```bash
curl http://localhost:8000/stickers/album/10
```

**Parámetros**:
- `numero_album` (path, requerido): Número del álbum (1-638)

**Respuesta** (200):
```json
[
  {
    "id": 10,
    "nombre": "Neymar",
    "pais": "Brasil",
    "rareza": "raro",
    "numero_album": 10,
    "coleccionado": false
  },
  ...
]
```

## Observabilidad: Cómo Funciona

### Arquitectura de Telemetría

La observabilidad está implementada en 3 capas:

```
Layer 1: Aplicaciones (sticker-api, sticker-db-service)
  └─> Instrumentadores OpenTelemetry (auto + manual)
       ├─ FastAPIInstrumentor: captura HTTP requests/responses
       ├─ HTTPXInstrumentor: propaga contexto en HTTP calls
       ├─ AsyncPGInstrumentor: traza queries SQL
       └─ LoggingInstrumentor: inyecta trace_id en logs

Layer 2: OTLP Exporter (gRPC)
  └─> Envía spans, métricas, logs a OpenTelemetry Collector:4317

Layer 3: OpenTelemetry Collector (Procesamiento)
  └─> Processors: memory_limiter, batch
       Exporters: New Relic (producción) + debug (desarrollo)
```

### Qué se Instrumenta

#### 1. Trazas Distribuidas (Traces)

**Auto-capturadas**:
- Cada HTTP request a sticker-api genera un span raíz (`sticker-api`)
- La llamada HTTP a sticker-db-service genera un span hijo (`HTTP GET`)
- La query a PostgreSQL genera un span hijo (`query`)

**Spans Customizados (Manuales)**:
```python
# sticker-api/routes/stickers.py
with tracer.start_as_current_span("sticker.list") as span:
    span.set_attribute("sticker.pais", pais)
    span.set_attribute("sticker.rareza", rareza)
```

Esto añade semántica de negocio a las trazas. En New Relic verás:
```
Transaction: GET /stickers
  └─ Span: sticker.list [pais=Argentina, rareza=legendario]
     └─ Span: HTTP GET sticker-db-service:8001/stickers
        └─ Span: query (SELECT * FROM stickers WHERE ...)
```

**Propagación de Contexto**:
El trace_id se propaga via header `traceparent`:
```
traceparent: 00-[trace_id]-[span_id]-01
baggage: user_id=123,request_source=mobile
```

sticker-api → sticker-db-service mantiene el mismo trace_id, creando una cadena visible.

#### 2. Métricas

**Métricas Automáticas**:
- Histograma: `http.server.request.duration` (latencia por endpoint)
- Contador: `http.server.requests.total` (volumen por status)
- Gauge: `db.client.connections.usage` (pool connections activas)

**Métricas Customizadas**:
```python
request_counter = meter.create_counter(
    "sticker_requests_total",
    description="Total sticker API requests"
)
request_counter.add(1, {"endpoint": "list"})
```

En New Relic visualizarás:
- Requests por segundo por endpoint
- P50/P95/P99 latencia
- Error rate
- Database query time

#### 3. Logs Estructurados

Cada log incluye automáticamente:
```
timestamp: 2024-05-16T10:30:45.123Z
severity: INFO
message: "GET /stickers completed"
trace_id: "a1b2c3d4e5f6g7h8"  <-- Inyectado automáticamente
span_id: "x1y2z3a4"
service: "sticker-api"
```

En New Relic, clicar en una traza distribuida muestra los logs asociados (matched por trace_id).

### Configuración de OpenTelemetry

#### En los Servicios (setup_telemetry)

```python
# Tracer Provider con OTLP exporter
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)

# Meter Provider para métricas
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

# Propagación: W3C TraceContext + W3C Baggage
set_global_textmap(
    CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator()
    ])
)
```

**Environment variables**:
```bash
OTEL_SERVICE_NAME=sticker-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=dev
```

#### En el Collector (collector-config.yaml)

```yaml
receivers:
  otlp:
    protocols:
      grpc:  # Puerto 4317 (espera spans, métricas, logs)
      http:  # Puerto 4318 (alternativa JSON)

processors:
  memory_limiter:  # Previene OOM (256MB)
  batch:           # Agrupa antes de exportar (max 1024 items/s)

exporters:
  otlp/newrelic:
    endpoint: otlp.nr-data.net:4317
    headers:
      api-key: ${NEW_RELIC_LICENSE_KEY}
  debug:           # Salida local para debugging
```

## Verificación: ¿Llegan Datos a New Relic?

### 1. En Desarrollo (Logs del Collector)

```bash
docker-compose logs -f otel-collector | grep -i "span\|metric\|log"
```

Deberías ver spans similar a:
```
Span #0
  Trace ID   : a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
  Parent ID  : x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6
  ID         : 0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d
  Name       : sticker.list
  Attributes:
    sticker.pais: Argentina
```

### 2. En Producción (New Relic UI)

1. Ir a **New Relic Home > APM & Services**
2. Buscar servicios: `sticker-api`, `sticker-db-service`
3. Ver pestaña **Distributed Tracing**: transacciones completas con cadenas de spans
4. Ver pestaña **Logs**: logs correlacionados por trace_id

### 3. Generar Tráfico de Prueba

```bash
# Script simple para generar requests
for i in {1..100}; do
  curl "http://localhost:8000/stickers?pais=Argentina" &
done
wait
```

Luego verificar en:
- Logs del collector (desarrollo)
- New Relic Dashboard (producción)

### 4. Debugging: Port Forward del Collector Metrics

El collector expone métricas propias en puerto 8888:
```bash
curl http://localhost:8888/metrics | grep -i "otel"
```

Verás métricas como `otelcol_receiver_accepted_spans` (spans recibidos).

## Estructura del Repositorio

```
observabilidad-microservicios/
│
├── README.md                          # Este archivo
├── docker-compose.yml                 # Orquestación local (dev)
├── .env.example                       # Plantilla de variables de entorno
├── .gitignore                         # Archivos ignorados (secrets, .env)
│
├── sticker-api/                       # Microservicio Gateway
│   ├── app/
│   │   ├── main.py                    # FastAPI app + instrumentación
│   │   ├── models/
│   │   │   └── sticker.py             # Modelo de datos (Pydantic)
│   │   ├── routes/
│   │   │   └── stickers.py            # 3 endpoints GET (con spans manuales)
│   │   ├── services/
│   │   │   └── db_client.py           # Cliente HTTP a sticker-db-service
│   │   └── telemetry/
│   │       └── setup.py               # Configuración de OTEL (tracer, meter)
│   ├── Dockerfile                     # Build: Python 3.11, pip install
│   └── requirements.txt                # opentelemetry-*, fastapi, httpx, etc
│
├── sticker-db-service/                # Microservicio de Datos
│   ├── app/
│   │   ├── main.py                    # FastAPI app + instrumentación
│   │   ├── models/
│   │   │   └── sticker.py             # Modelo compartido
│   │   ├── routes/
│   │   │   └── stickers.py            # Endpoints (llamados por sticker-api)
│   │   ├── db/
│   │   │   └── pool.py                # asyncpg connection pool + queries
│   │   └── telemetry/
│   │       └── setup.py               # OTEL setup (idéntico a sticker-api)
│   ├── Dockerfile                     # Build: Python 3.11, pip install
│   ├── requirements.txt               # asyncpg, opentelemetry-*, etc
│   └── init.sql                       # Schema PostgreSQL (aplicada al iniciar)
│
├── otel-collector/
│   └── collector-config.yaml          # Configuración del OTel Collector
│                                       # - Receivers OTLP (gRPC + HTTP)
│                                       # - Processors (batch, memory_limiter)
│                                       # - Exporters (New Relic + debug)
│
├── k8s/                               # Manifests Kubernetes (AKS)
│   ├── namespace.yaml                 # Namespace "observabilidad"
│   ├── secrets.yaml                   # Credenciales (ignorado en git)
│   ├── secrets.yaml.example           # Plantilla de secrets
│   ├── configmaps/
│   │   ├── otel-collector.yaml        # Config del collector para K8s
│   │   └── postgres-init.yaml         # Schema SQL como ConfigMap
│   ├── pvc/
│   │   └── postgres.yaml              # PersistentVolumeClaim (1Gi, Azure CSI)
│   ├── deployments/
│   │   ├── postgres.yaml              # StatefulSet PostgreSQL 16
│   │   ├── sticker-api.yaml           # Deployment (1 replica, 250m CPU, 256Mi RAM)
│   │   ├── sticker-db-service.yaml    # Deployment (1 replica)
│   │   └── otel-collector.yaml        # Deployment del collector
│   ├── services/
│   │   ├── postgres.yaml              # ClusterIP, puerto 5432
│   │   ├── sticker-api.yaml           # ClusterIP, puerto 8000
│   │   ├── sticker-db-service.yaml    # ClusterIP, puerto 8001
│   │   └── otel-collector.yaml        # ClusterIP, puerto 4317 (gRPC)
│   └── ingress/
│       └── sticker-api.yaml           # Ingress (nginx), host sticker-api.local
│
└── scripts/
    └── load_test.py                   # Script de testing/carga (opcional)
```

## Notas sobre la Implementación

### Variables de Entorno

**Servicios OpenTelemetry**:
```bash
OTEL_SERVICE_NAME          # Nombre del servicio (sticker-api, sticker-db-service)
OTEL_EXPORTER_OTLP_ENDPOINT # URL del collector (http://otel-collector:4317)
OTEL_RESOURCE_ATTRIBUTES   # Atributos de recurso (version, environment)
NEW_RELIC_LICENSE_KEY      # Token New Relic (en Secret K8s o .env local)
```

**Base de Datos**:
```bash
DATABASE_URL        # Connection string PostgreSQL (asyncpg format)
POSTGRES_PASSWORD   # Password de PostgreSQL
```

**API Gateway**:
```bash
DB_SERVICE_URL      # URL de sticker-db-service (http://sticker-db-service:8001)
```

### Problemas Conocidos y Soluciones

| Problema | Solución |
|----------|----------|
| Import error `set_global_textformat_propagator` | Usar `set_global_textmap` (cambio en v1.24.0+) |
| Exporter `logging` deprecated | Usar exporter `debug` en collector-config.yaml |
| `memory_limiter` sin `check_interval` falla | Agregar `check_interval: 1s` (obligatorio) |
| PostgreSQL en K8s no inicia en Azure CSI | Mover PGDATA a `pgdata/` subdirectorio del volumen |
| Secret K8s tiene placeholder `replace_me` | Actualizar con valor real: `kubectl set env deployment/... -n observabilidad` |

## Comandos Útiles

### Docker Compose

```bash
# Levantar servicios
docker-compose up -d

# Ver logs de un servicio
docker-compose logs -f sticker-api
docker-compose logs -f otel-collector

# Detener sin eliminar volúmenes
docker-compose stop

# Detener y eliminar todo
docker-compose down

# Reconstruir imágenes
docker-compose build --no-cache
```

### Kubernetes

```bash
# Ver estado de pods
kubectl get pods -n observabilidad
kubectl describe pod <pod-name> -n observabilidad

# Ver logs de un pod
kubectl logs -f <pod-name> -n observabilidad

# Port-forward para debugging
kubectl port-forward svc/sticker-api 8000:8000 -n observabilidad

# Escalar deployment
kubectl scale deployment sticker-api --replicas=3 -n observabilidad

# Actualizar imagen sin reconstruir manifest
kubectl set image deployment/sticker-api sticker-api=<registry>/sticker-api:v2 -n observabilidad

# Eliminar namespace (elimina todo)
kubectl delete namespace observabilidad
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Listar stickers (todos)
curl http://localhost:8000/stickers

# Listar stickers (filtrado)
curl "http://localhost:8000/stickers?pais=Argentina&rareza=legendario"

# Obtener sticker por ID
curl http://localhost:8000/stickers/1

# Stickers por número de álbum
curl http://localhost:8000/stickers/album/10
```

## Consideraciones de Producción

### Escalabilidad
- Los servicios son stateless y escalables horizontalmente vía `kubectl scale`
- AsyncPG maneja concurrencia eficiente (event loop async)
- El Collector puede tener cuello de botella; considerar múltiples collectors con load balancer en cargas altas

### Seguridad
- New Relic License Key debe estar en Secret K8s (no en ConfigMap)
- PostgreSQL password en Secret K8s, no en deployment
- Ingress debe usar TLS en producción (agregar certificado)
- Limitar acceso a puertos internos (4317, 5432) vía NetworkPolicy

### Observabilidad de la Observabilidad
- Monitorear métricas del collector: `otelcol_receiver_accepted_spans`, `otelcol_exporter_sent_spans`
- Alertar si spans droppados > 0 (indica pérdida de telemetría)
- Verificar latencia del collector (debe ser <100ms)

## Referencias

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [New Relic OTLP Endpoint](https://docs.newrelic.com/docs/more-integrations/open-source-integrations/opentelemetry/opentelemetry-introduction/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [AsyncPG](https://magicstack.github.io/asyncpg/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)

## Licencia

Este es un proyecto educativo/académico. Úsalo como referencia para tu propia arquitectura de observabilidad.

---

**Última actualización**: Mayo 2024

Para preguntas o mejoras, consulta con el equipo de desarrollo.
