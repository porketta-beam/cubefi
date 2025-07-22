"""LangSmith monitoring module for RAG system observability"""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from langsmith import Client, traceable


class LangSmithMonitor:
    """LangSmith monitoring wrapper with OpenTelemetry integration"""
    
    def __init__(self):
        self.client = None
        self.tracer = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LangSmith and OpenTelemetry clients"""
        try:
            # LangSmith client initialization
            api_key = os.getenv("LANGSMITH_API_KEY")
            project = os.getenv("LANGSMITH_PROJECT", "rag_lab_project")
            
            if api_key and api_key != "your_langsmith_api_key_here":
                self.client = Client(api_key=api_key)
                print(f"LangSmith initialized for project: {project}")
            else:
                print("LangSmith API key not configured, monitoring disabled")
                
            # OpenTelemetry tracer initialization
            if not os.getenv("OTEL_SDK_DISABLED", "false").lower() == "true":
                # Set tracer provider
                tracer_provider = TracerProvider()
                trace.set_tracer_provider(tracer_provider)
                
                # Configure OTLP exporter if endpoint is provided
                otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
                if otlp_endpoint:
                    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                    span_processor = BatchSpanProcessor(otlp_exporter)
                    tracer_provider.add_span_processor(span_processor)
                
                self.tracer = trace.get_tracer(__name__)
                print("OpenTelemetry tracer initialized")
            else:
                print("OpenTelemetry disabled via OTEL_SDK_DISABLED")
                
        except Exception as e:
            print(f"Error initializing monitoring clients: {e}")
    
    @contextmanager
    def trace_span(self, name: str, **kwargs):
        """Context manager for creating traced spans"""
        span_context = None
        
        try:
            # Start OpenTelemetry span
            if self.tracer:
                span_context = self.tracer.start_span(name)
                span_context.__enter__()
                
                # Add custom attributes to span
                for key, value in kwargs.items():
                    span_context.set_attribute(key, str(value))
            
            yield {
                "span": span_context,
                "run": None,
                "run_id": None
            }
            
        except Exception as e:
            # Record error in spans
            if span_context:
                span_context.record_exception(e)
                span_context.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
            
        finally:
            # End contexts
            if span_context:
                try:
                    span_context.__exit__(None, None, None)
                except Exception as e:
                    print(f"Error ending OpenTelemetry span: {e}")
    
    def log_metrics(self, metrics: Dict[str, Any], operation: str = "general"):
        """Log custom metrics to LangSmith"""
        if not self.client:
            return
            
        try:
            self.client.create_run(
                name=f"metrics_{operation}",
                project_name=os.getenv("LANGSMITH_PROJECT", "rag_lab_project"),
                run_type="tool",
                inputs={"operation": operation},
                outputs=metrics
            )
        except Exception as e:
            print(f"Error logging metrics to LangSmith: {e}")
    
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.client is not None or self.tracer is not None


# Global monitor instance
_monitor = LangSmithMonitor()


def trace_span(name: str, **kwargs):
    """Convenience function for creating traced spans"""
    return _monitor.trace_span(name, **kwargs)


def log_metrics(metrics: Dict[str, Any], operation: str = "general"):
    """Convenience function for logging metrics"""
    return _monitor.log_metrics(metrics, operation)


def get_tracer():
    """Get the OpenTelemetry tracer instance"""
    return _monitor.tracer


def get_client():
    """Get the LangSmith client instance"""
    return _monitor.client


def is_monitoring_enabled() -> bool:
    """Check if monitoring is enabled"""
    return _monitor.is_enabled()


# Initialize monitoring on module import
try:
    with trace_span("langsmith_monitor_init") as context:
        print(f"LangSmith monitor module loaded. Monitoring enabled: {is_monitoring_enabled()}")
        if context.get("run_id"):
            print(f"Initial trace run ID: {context['run_id']}")
except Exception as e:
    print(f"Error during monitor initialization: {e}")