import time
import logging
from typing import Optional

# Setup standard logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("NOVA_Automation")

class AutomationLogger:
    """Provides structured logging for the NOVA Automation system."""
    
    @staticmethod
    def info(
        action: str,
        target: str,
        duration_ms: float,
        retries: int = 0,
        verification: str = "None",
        status: str = "Success",
        failure_reason: Optional[str] = None
    ) -> None:
        """Log details of a completed automation action in a structured layout."""
        log_parts = [
            f"action={action}",
            f"target={target}",
            f"duration={duration_ms:.2f}ms",
            f"retries={retries}",
            f"verification={verification}",
            f"status={status}"
        ]
        if failure_reason:
            log_parts.append(f"reason={failure_reason}")
            
        msg = "[AUTOMATION] " + " | ".join(log_parts)
        logger.info(msg)

    @staticmethod
    def warning(msg: str) -> None:
        logger.warning(f"[AUTOMATION] {msg}")

    @staticmethod
    def error(msg: str) -> None:
        logger.error(f"[AUTOMATION] {msg}")
