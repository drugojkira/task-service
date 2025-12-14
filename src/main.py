import asyncio

from uvicorn import Config, Server

from task_service.app import create_app
from task_service.core.config import settings
from task_service.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = create_app()


async def run() -> None:
    """Запуск сервера."""
    logger.info("Starting Task Service...")

    config = Config(
        app,
        host="0.0.0.0",
        port=settings.PORT,
    )
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run())
