import contextvars
import json
import logging

from {{ package_name }}.config import Settings

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "trace_id": trace_id_var.get(),
        }
        if hasattr(record, "context"):
            payload.update(record.context)
        return json.dumps(payload)


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        JSONFormatter()
        if settings.app_env == "production"
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
