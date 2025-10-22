#pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http opentelemetry-exporter-otlp-proto-grpc

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
#from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind

# Configurar el TracerProvider
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configurar el exporter hacia el OpenTelemetry Collector OTLP/gRPC
exporter = OTLPSpanExporter(
    endpoint="otel-collector.test-istio-v3.svc.cluster.local:4317",
    #certificate_file="/tmp/tempo.crt"
    insecure=True  # Cambiar si usas TLS válido
)

span_processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Crear y enviar una traza simple
with tracer.start_as_current_span("test-span", kind=SpanKind.INTERNAL) as span:
    span.set_attribute("example.attribute", "value")
    print("Tracer: Span creado y enviado")

import time
time.sleep(5)  # Esperar a que el span se exporte
