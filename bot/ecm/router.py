from maxapi.dispatcher import Router
from maxapi.types import BotStarted
from utils.rc4_utils import decrypt_rc4
from logger import logger
from config import settings
from utils.ecm import ecm_client


router = Router(router_id="ecm_router")


@router.bot_started()
async def on_bot_started(event: BotStarted) -> None:
    logger.info(event)
    max_id = event.user.user_id
    payload = event.payload

    if payload is not None:
        try:
            decrypted_payload = decrypt_rc4(payload, settings.SECRET_KEY)
            user_id = decrypted_payload.split("_", 1)[1]
            await ecm_client.ecos_change_user_max_id(max_id, user_id)
            await event.bot.send_message(
                user_id=max_id,
                text="Привет! Я сохранил твой MAX ID в ECM.",
            )
            logger.info(
                "Saved max_id to ecm",
                exc_info=True,
                extra={"max_id": max_id, "user_id": user_id},
            )
        except Exception as e:
            logger.warning(
                f"FAILED to save max_id to ecm {e}",
                exc_info=True,
                extra={"max_id": max_id, "user_id": user_id},
            )
            await event.bot.send_message(
                user_id=max_id,
                text="Привет! Я не смог сохранить твой MAX ID в ECM.",
            )
    else:
        await event.bot.send_message(
            user_id=max_id,
            text="Привет! Рад приветствовать тебя в ИТ.Москве!",
        )
