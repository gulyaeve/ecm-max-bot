from httpx import AsyncClient
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted

from config import settings
from logger import logger
from utils.ecm import ECMClient
from utils.rc4_utils import decrypt_rc4


bot = Bot(settings.MAX_BOT_TOKEN)
dp = Dispatcher()
http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)


@dp.bot_started()
async def on_bot_started(event: BotStarted) -> None:
    logger.info(event)
    max_id = event.user.user_id
    payload = event.payload

    if payload is not None:
        try:
            decrypted_payload = decrypt_rc4(payload, settings.SECRET_KEY)
            user_id = decrypted_payload.split("_", 1)[1]
            await ecm_client.ecos_change_user_max_id(max_id, user_id)
            await bot.send_message(
                user_id=max_id,
                text="Привет! Я сохранил твой MAX ID в ECM.",
            )
            logger.info("Saved max_id to ecm", exc_info=True, extra={"max_id": max_id, "user_id": user_id})
        except Exception as e:
            logger.warning(f"FAILED to save max_id to ecm {e}", exc_info=True, extra={"max_id": max_id, "user_id": user_id})
            await bot.send_message(
                user_id=max_id,
                text="Привет! Я не смог сохранить твой MAX ID в ECM.",
            )
    else:
        await bot.send_message(
            user_id=max_id,
            text="Привет! Рад приветствовать тебя в ИТ.Москве!",
        )


async def main():
    logger.info("Hello from ecm-max-bot!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    from asyncio import run
    run(main())
