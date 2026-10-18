import uvicorn

from freeeval.api.app import create_app
from freeeval.config import Settings
from freeeval.logging_config import get_logger, setup_logging

logger = get_logger("freeeval")


def main() -> None:
    settings = Settings()
    setup_logging(level=settings.log_level)
    logger.info("environment=%s", settings.environment)
    uvicorn.run(
        create_app(),
        host=settings.host,
        port=settings.port,
        log_config=None,
    )
