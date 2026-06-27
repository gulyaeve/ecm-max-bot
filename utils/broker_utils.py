from config import settings
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker


result_backend = RedisAsyncResultBackend(redis_url=settings.redis_url)

broker = RedisStreamBroker(url="redis://localhost:6379/0").with_result_backend(
    result_backend
)

