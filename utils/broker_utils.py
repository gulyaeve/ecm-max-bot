from asyncio import run
from concurrent.futures import ProcessPoolExecutor

from bot.mosru.depends import report_process_to_ecm

# from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

# from config import settings

# result_backend = RedisAsyncResultBackend(redis_url=settings.redis_url)

# broker = RedisStreamBroker(url=settings.redis_url).with_result_backend(result_backend)

process_pool = ProcessPoolExecutor(max_workers=4)


def sync_ecm_report(token: str):
    # Запускаем асинхронную функцию внутри отдельного процесса
    return run(report_process_to_ecm(token))
