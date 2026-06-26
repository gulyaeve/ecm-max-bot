from maxapi.dispatcher import Router
from maxapi import F
from maxapi.types import Command, InputMedia, MessageCreated
from bot.mosru.depends import create_report_xlsx
from utils.ecm import ecm_client
from config import settings
from utils.redis import redis_client
from logger import logger


router = Router(router_id="mosru")


@router.message_created(F.message.body.text.startswith("token"))
async def save_token(event: MessageCreated):
    ecm_user_login = await ecm_client.get_user_login_from_ecm(event.from_user.user_id)
    if ecm_user_login == settings.ECM_LOGIN_MOSRU_TOKEN:
        try:
            token = event.message.body.text.split("token_", 1)[1]
            async with redis_client as cache:
                await cache.set("mosru_token", token)
                token_value_from_redis = await cache.get("mosru_token")

            logger.info(f"mosru token saved in redis {token_value_from_redis}")

            await event.message.answer(
                text=f"Токен для {settings.ECM_LOGIN_MOSRU_TOKEN} сохранён",
            )
        except Exception as e:
            logger.warning(f"mosru token DOES NOT SAVE in redis {token} {e}")

            await event.message.answer(
                text=f"Не смог сохранить токен для {settings.ECM_LOGIN_MOSRU_TOKEN}",
            )


@router.message_created(Command("report"))
async def send_file_with_reports(event: MessageCreated):
    ecm_user_login = await ecm_client.get_user_login_from_ecm(event.from_user.user_id)

    if ecm_user_login in settings.ECM_LOGINS_FOR_REPORT:
        try:
            # file_path = await create_reports_zip()
            async with redis_client as cache:
                token = await cache.get("mosru_token")
            file_path = await create_report_xlsx(token)

            media = InputMedia(file_path)
            await event.message.answer(
                text="Отчёты по приоритетам", attachments=[media]
            )
        except Exception as e:
            logger.warning(f"Report create error {e}")
            await event.message.answer("Произошла ошибка при формировании отчёта")
