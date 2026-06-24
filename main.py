from maxapi import Bot, Dispatcher

from config import settings
from logger import logger
from bot.mosru.router import router as mosru_router
from bot.ecm.router import router as ecm_router


bot = Bot(settings.MAX_BOT_TOKEN)
dp = Dispatcher()


dp.include_routers(
    mosru_router,
    ecm_router,
)


async def main():
    logger.info("Hello from ecm-max-bot!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    from asyncio import run

    run(main())
