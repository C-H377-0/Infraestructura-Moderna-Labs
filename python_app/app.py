import os
from flask import Flask, request
import psycopg2
import logging
import time
import socket
import requests
import json
import traceback

# Importar el exportador de Prometheus para Flask
from prometheus_flask_exporter import PrometheusMetrics

# Configura el logging basico para la aplicacion
# Esto mostrara los logs generales de la aplicacion y los logs internos de OpenTelemetry
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuracion manual del logger Loki
def enviar_log_a_loki(mensaje, level="info", exc=None):
    """
    Envia logs a una instancia de Loki.
    Incluye el nombre del host y detalles de la excepcion si se proporcionan.
    """
    now_ns = str(int(time.time() * 1e9))  # Timestamp en nanosegundos

    # Si se incluye una excepcion, agregamos el stacktrace para una mejor depuracion
    if exc:
        mensaje += f"\nTipo de error: {type(exc).__name__}\n"
        mensaje += f"Mensaje: {str(exc)}\n"
        mensaje += f"Stacktrace:\n{traceback.format_exc()}"

    payload = {
        "streams": [
            {
                "stream": {
                    "app": "python_app",
                    "level": level,
                    "host": socket.gethostname() # Agrega el nombre del host para una mejor identificacion en Loki
                },
                "values": [
                    [ now_ns, mensaje ]
                ]
            }
        ]
    }

    try:
        # Intenta enviar el payload del log a Loki
        r = requests.post(
            "http://loki:3100/loki/api/v1/push",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        if r.status_code != 204:
            # Registra un error si Loki responde con un codigo de estado diferente de 204
            logger.error(f"?? Loki respondio con codigo {r.status_code}: {r.text}")
    except Exception as e:
        # Registra cualquier excepcion que ocurra durante el proceso de envio del log
        logger.error(f"? Error enviando log a Loki: {e}")

# Configuracion de Flask + OpenTelemetry
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Define los atributos de recurso para tu servicio.
# Estos atributos ayudan a identificar tu servicio en sistemas de tracing como Tempo.
resource = Resource.create({
    "service.name": "python-flask-app",
    "service.version": "1.0.0",
    "host.name": socket.gethostname() # Incluye el nombre del host en el recurso para un mejor contexto
})

# Establece el proveedor global de trazas con el recurso definido
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configura el exportador de Spans OTLP para Tempo.
# Es una buena practica usar una variable de entorno para el endpoint,
# proporcionando un valor predeterminado si no se establece.
# El endpoint HTTP OTLP estandar para Tempo es http://tempo:4318/v1/traces.
tempo_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4318/v1/traces")
logger.info(f"Configurando OTLP Span Exporter con endpoint: {tempo_endpoint}")

otlp_exporter = OTLPSpanExporter(endpoint=tempo_endpoint)
# BatchSpanProcessor es eficiente para produccion ya que envia los spans en lotes.
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# --- SOLO PARA DEPURACIoN ---
# Descomenta la siguiente linea para exportar tambien los spans a la consola.
# Esto es util para verificar si los spans se estan generando en absoluto.
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
# --- FIN DEPURACIoN ---


app = Flask(__name__)
# Inicializa PrometheusMetrics para tu aplicacion Flask
# Esto creara automaticamente metricas como http_requests_total, http_request_duration_seconds, etc.
# y las expondra en el endpoint /metrics por defecto.
metrics = PrometheusMetrics(app)
# Instrumenta Flask para crear automaticamente spans para las solicitudes entrantes
FlaskInstrumentor().instrument_app(app)
# Instrumenta Psycopg2 para crear automaticamente spans para las operaciones de base de datos
Psycopg2Instrumentor().instrument()

@app.route("/")
def hello():
    """
    Endpoint raiz para la aplicacion Flask.
    """
    enviar_log_a_loki("? Acceso al endpoint raiz /")
    logger.info("Accediendo al endpoint raiz /")
    return "Hola desde Python Flask"

@app.route("/insertar", methods=["POST"])
def insertar():
    """
    Endpoint para insertar datos de contacto en la base de datos PostgreSQL.
    Si el nombre es 'error' (sin importar mayúsculas), se intenta insertar en una tabla inexistente para provocar un error.
    """
    nombre = request.form.get("nombre")
    telefono = request.form.get("telefono")
    enviar_log_a_loki(f"?? Intentando insertar: {nombre} - {telefono}")
    logger.info(f"Intentando insertar: {nombre} - {telefono}")

    try:
        with tracer.start_as_current_span("InsertarContacto"):
            conn = psycopg2.connect(
                host="postgres",
                dbname="labdb",
                user="labuser",
                password="labpass"
            )
            cur = conn.cursor()

            # Si el nombre es 'error' (en cualquier capitalización), se provoca un error intencional
            if nombre and nombre.strip().lower() == "error":
                cur.execute("INSERT INTO contactos_error (nombre, telefono) VALUES (%s, %s);", (nombre, telefono))  # Esta tabla NO debe existir
            else:
                cur.execute("INSERT INTO contactos (nombre, telefono) VALUES (%s, %s);", (nombre, telefono))

            conn.commit()
            cur.close()
            conn.close()

            enviar_log_a_loki("✅ Datos insertados correctamente")
            logger.info("Datos insertados correctamente")
            return "Datos insertados correctamente"
    except Exception as e:
        enviar_log_a_loki("❌ Error al insertar datos", level="error", exc=e)
        logger.error("Error al insertar datos", exc_info=True)
        return "Error al insertar datos", 500

if __name__ == "__main__":
    enviar_log_a_loki("?? Iniciando aplicacion Flask en puerto 5000")
    logger.info("Iniciando aplicacion Flask en el puerto 5000")
    # Ejecuta la aplicacion Flask, accesible desde cualquier IP (0.0.0.0) en el puerto 5000
    app.run(host="0.0.0.0", port=5000)
