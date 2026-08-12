from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracing(console: bool = False):
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        return trace.get_tracer("ai-sales-coach")
    provider = TracerProvider(resource=Resource.create({"service.name": "ai-sales-coach"}))
    if console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ai-sales-coach")
