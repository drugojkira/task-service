from typing import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from faststream.rabbit import RabbitBroker
from redis.asyncio import Redis

from task_service.core.config import settings
from task_service.domain.metrics.use_case import GetTasksMetricsUseCase
from task_service.domain.use_cases.create_task import CreateTaskUseCase
from task_service.domain.use_cases.create_comment import CreateCommentUseCase
from task_service.domain.use_cases.delete_task import DeleteTaskUseCase
from task_service.domain.use_cases.get_tasks import GetTasksUseCase
from task_service.domain.use_cases.get_task_comments import GetTaskCommentsUseCase
from task_service.domain.use_cases.update_task import UpdateTaskUseCase
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.comment_repository import CommentRepository
from task_service.infrastructure.rabbitmq.broker import broker
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.kafka.publisher import KafkaPublisher


class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    def get_database(self) -> Database:
        return Database(settings.postgres_url)

    @provide
    def get_rabbit_broker(self) -> RabbitBroker:
        return broker

    @provide
    async def get_redis(self) -> AsyncIterator[Redis]:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        yield redis
        await redis.aclose()

    @provide
    async def get_kafka_publisher(self) -> AsyncIterator[KafkaPublisher]:
        publisher = KafkaPublisher(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_TASK_EVENTS,
            enabled=settings.KAFKA_ENABLED,
        )
        await publisher.start()
        yield publisher
        await publisher.stop()


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_task_repository(self) -> TaskRepository:
        return TaskRepository()

    @provide
    def get_redis_repository(self) -> RedisRepository:
        return RedisRepository()
    
    @provide
    def get_comment_repository(self) -> CommentRepository:
        return CommentRepository()


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_rabbitmq_publisher(self, broker: RabbitBroker) -> RabbitMQPublisher:
        return RabbitMQPublisher(broker)


class UseCaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_create_task(
        self,
        database: Database,
        repository: TaskRepository,
        publisher: RabbitMQPublisher,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
    ) -> CreateTaskUseCase:
        return CreateTaskUseCase(database, repository, publisher, cache, kafka_publisher)

    @provide
    def get_get_tasks(
        self,
        database: Database,
        repository: TaskRepository,
        cache: RedisRepository,
    ) -> GetTasksUseCase:
        return GetTasksUseCase(database, repository, cache)

    @provide
    def get_update_task(
        self,
        database: Database,
        repository: TaskRepository,
        publisher: RabbitMQPublisher,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
    ) -> UpdateTaskUseCase:
        return UpdateTaskUseCase(database, repository, publisher, cache, kafka_publisher)

    @provide
    def get_delete_task(
        self,
        database: Database,
        repository: TaskRepository,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
    ) -> DeleteTaskUseCase:
        return DeleteTaskUseCase(database, repository, cache, kafka_publisher)

    @provide
    def get_create_comment(self, database: Database, repository: CommentRepository) -> CreateCommentUseCase:
        return CreateCommentUseCase(database, repository)

    @provide
    def get_get_task_comments(self, database: Database, repository: CommentRepository) -> GetTaskCommentsUseCase:
        return GetTaskCommentsUseCase(database, repository)


class MetricsProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_tasks_metrics(
        self,
        database: Database,
        repository: TaskRepository,
    ) -> GetTasksMetricsUseCase:
        return GetTasksMetricsUseCase(database, repository)


container = make_async_container(
    InfrastructureProvider(),
    RepositoryProvider(),
    ServiceProvider(),
    UseCaseProvider(),
    MetricsProvider(),
)
