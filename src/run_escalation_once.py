import asyncio

from task_service.core.providers.setup import container
from task_service.domain.use_cases.auto_escalate_tasks import AutoEscalateTasksUseCase
from task_service.infrastructure.rabbitmq.broker import broker


async def main() -> None:
    await broker.connect()
    try:
        async with container() as request_container:
            use_case = await request_container.get(AutoEscalateTasksUseCase)
            result = await use_case.execute()
            print(result)
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())

