import logging
import sys

import structlog
from rich.console import Console
from structlog.dev import RichTracebackFormatter

def configure_logging(
    log_level:str,
    environment:str
) -> None :
    level = getattr(
        logging,
        log_level.upper(),
        logging.INFO,
    )
    timestamper = structlog.processors.TimeStamper(
        fmt="iso",
        utc=True
    )
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.format_exc_info,
    ]
    
    if environment == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors = True,
            exception_formatter = RichTracebackFormatter(
                show_locals = False
            ),
        )
    
    structlog.configure(
        processors = [
            *shared_processors,
            renderer,
        ],
        wrapper_class  = structlog.make_filtering_bound_logger(
            level,
        ),
        logger_factory = structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream = sys.stdout,
        level = level,
        force = True
    )
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING
    )
    logging.getLogger("uvicorn.error").setLevel(
        level
    )
    if environment != "production":
        Console()