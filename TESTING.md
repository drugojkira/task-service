# Тестирование Task Statistics Feature

Этот документ описывает как проверить что счётчики задач работают правильно.

## Структура тестов

### 1. Unit тесты Use Case (`tests/domain/use_cases/test_get_task_statistics.py`)
Проверяют логику получения статистики:
- ✅ Cache hit: повторный запрос возвращает из кэша
- ✅ Cache miss: первый запрос читает из БД и кэширует результат
- ✅ Корректность расчёта статистики
- ✅ TTL кэша (1 минута)

### 2. API тесты (`tests/api/test_tasks.py`)
Проверяют endpoint `GET /api/v1/tasks/statistics`:
- ✅ Успешное получение статистики (HTTP 200)
- ✅ Формат ответа с полями: total_tasks, by_status, by_priority, by_assignee
- ✅ Получение статистики при пустом списке задач

### 3. Тесты инвалидации кэша (`tests/infrastructure/test_cache_invalidation.py`)
Проверяют что кэш статистики инвалидируется при изменении задач:
- ✅ Создание задачи инвалидирует кэш
- ✅ Обновление задачи инвалидирует кэш
- ✅ Удаление задачи инвалидирует кэш

## Запуск тестов

### Все тесты
```bash
cd task-service
pytest
```

### Только Unit тесты статистики
```bash
pytest tests/domain/use_cases/test_get_task_statistics.py -v
```

### Только API тесты статистики
```bash
pytest tests/api/test_tasks.py::TestTasksAPI::test_get_task_statistics_success -v
pytest tests/api/test_tasks.py::TestTasksAPI::test_get_task_statistics_empty -v
```

### Только тесты инвалидации
```bash
pytest tests/infrastructure/test_cache_invalidation.py -v
```

### С покрытием кода
```bash
pytest --cov=task_service --cov-report=html
open htmlcov/index.html
```

## Локальное тестирование (интеграционное)

### 1. Запустить Docker Compose
```bash
cd composer
docker-compose up -d
```

Проверить что контейнеры запущены:
```bash
docker ps
```

### 2. Запустить миграции в task-service
```bash
cd ../task-service
alembic upgrade head
```

### 3. Запустить сервис локально
```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить
python -m src.main
# или через make
make run
```

Сервис запустится на `http://localhost:8000`

### 4. Тестировать API

#### Создать задачу
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: test-user" \
  -d '{
    "title": "Task 1",
    "description": "Test task",
    "priority": "high",
    "assignee": "user1"
  }'
```

#### Создать ещё несколько задач (для статистики)
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: test-user" \
  -d '{
    "title": "Task 2",
    "description": "Test task 2",
    "priority": "medium",
    "assignee": "user2"
  }'

curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: test-user" \
  -d '{
    "title": "Task 3",
    "description": "Test task 3",
    "priority": "low"
  }'
```

#### Получить статистику (первый запрос - из БД)
```bash
curl http://localhost:8000/api/v1/tasks/statistics
```

Ответ должен быть:
```json
{
  "total_tasks": 3,
  "by_status": {
    "todo": 3
  },
  "by_priority": {
    "high": 1,
    "medium": 1,
    "low": 1
  },
  "by_assignee": {
    "user1": 1,
    "user2": 1
  }
}
```

#### Повторный запрос (должен вернуться из кэша)
```bash
curl http://localhost:8000/api/v1/tasks/statistics
```

Должен вернуть тот же результат очень быстро (< 10ms вместо > 50ms из БД).

Проверить в логах:
```
Cache hit: task statistics
```

#### Обновить задачу (инвалидирует кэш)
```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-User-Name: test-user" \
  -d '{
    "status": "in_progress"
  }'
```

#### Запрос статистики после обновления (новый запрос из БД)
```bash
curl http://localhost:8000/api/v1/tasks/statistics
```

Проверить в логах:
```
Cache miss: task statistics
```

#### Удалить задачу (инвалидирует кэш)
```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/1 \
  -H "X-User-Name: test-user"
```

#### Запрос статистики после удаления (новый запрос из БД)
```bash
curl http://localhost:8000/api/v1/tasks/statistics
```

Должен показать 2 задачи вместо 3.

## Проверка Redis кэша

### Подключиться к Redis
```bash
redis-cli

# Или через Docker
docker exec -it redis redis-cli
```

### Проверить что статистика кэшируется
```bash
# В Redis CLI
KEYS *
GET task_statistics
TTL task_statistics  # должно показать оставшееся время жизни (макс 60 сек)
```

## Проверка логов

Включить DEBUG логирование:

```python
# В core/config.py установить
LOG_LEVEL = "DEBUG"
```

Тогда в логах будут:
```
Cache hit: task statistics
Cache miss: task statistics
```

## Performance проверка

### Время ответа
1. **Первый запрос (cache miss)**: ~50-200ms (читает из БД)
2. **Повторные запросы (cache hit)**: ~5-10ms (из Redis)

Собрать метрики можно через Prometheus:
```bash
curl http://localhost:8000/metrics
```

## Интеграционный тест с Postman

Импортировать коллекцию:
```json
{
  "info": {
    "name": "Task Statistics",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Create Task 1",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/api/v1/tasks",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "X-User-Name", "value": "test-user"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"title\": \"Task 1\", \"priority\": \"high\", \"assignee\": \"user1\"}"
        }
      }
    },
    {
      "name": "Get Statistics",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/tasks/statistics"
      }
    }
  ]
}
```

## Проверка фиксов ошибок

### Если тесты падают

1. **Import ошибки**: CheckTaskStatistics импортируется правильно?
   ```bash
   python -c "from task_service.schemas.task import TaskStatistics; print(TaskStatistics)"
   ```

2. **Redis недоступен**: проверить что Redis запущен
   ```bash
   docker ps | grep redis
   redis-cli ping  # должно вернуть "PONG"
   ```

3. **БД недоступна**: проверить что PostgreSQL запущен
   ```bash
   docker ps | grep postgres
   ```

4. **DDL ошибки**: нужны миграции?
   ```bash
   alembic upgrade head
   ```

## Успешные индикаторы

✅ Все UNIT тесты проходят green  
✅ All API тесты проходят  
✅ Cache hit ratio > 80%  
✅ Response time: cache hit < 10ms, cache miss < 200ms  
✅ Кэш инвалидируется при изменении задач  
✅ TTL соблюдается (1 минута)  

## Debug комманды

```bash
# Проверить конфиг
python -c "from task_service.core.config import settings; print(settings.redis_url)"

# Проверить БД соединение
python -c "from task_service.infrastructure.postgres.database import Database; print('OK')"

# Запустить один тест с выводом
pytest tests/domain/use_cases/test_get_task_statistics.py::TestGetTaskStatisticsUseCase::test_cache_hit -v -s
```
