from datetime import datetime
from pathlib import Path

from maxapi.dispatcher import Router
from maxapi import F
from maxapi.types import MessageCreated
from utils.ecm import ecm_client
from config import settings
from utils.http_utils import download_file_http
from utils.redis import redis_client
from logger import logger


router = Router(router_id="mosru")


UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(exist_ok=True)




@router.message_created(F.message.body.text.startswith("token"))
async def save_token(event: MessageCreated):
    ecm_user_login = await ecm_client.get_user_login_from_ecm(event.from_user.user_id)
    if ecm_user_login == settings.ECM_LOGIN_MOSRU_TOKEN:
        token = event.message.body.text.split("token_", 1)[1]
        async with redis_client as cache:
            await cache.set("mosru_token", token)
            token_value_from_redis = await cache.get("mosru_token")

        logger.info(f"mosru token saved in redis {token_value_from_redis}")

        excel_file = await download_file_http(
            url="https://prof.mos.ru/back/api/applications/report",
            token=token_value_from_redis,
            json={"learningYearId":1002678188,"rklCheckStatuses":[],"applicationPriority":[],"page":0,"size":10,"sort":["registrationDateTime,desc"]}
        )

        file_path = UPLOAD_DIR / f"{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx"

        with open(file_path, "wb") as f:
            f.write(excel_file.getvalue())

        await event.message.answer(
            text=f"Я сохранил таблицу в {file_path}",
        )