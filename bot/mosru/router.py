from maxapi.dispatcher import Router
from maxapi import F
from maxapi.types import InputMediaBuffer, MessageCreated
from utils.ecm import ecm_client
from config import settings
from utils.http_utils import download_file_http
from utils.redis import redis_client
from logger import logger


router = Router(router_id="mosru")


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
            json={"learningYearId":1002678612,"rklCheckStatuses":[],"applicationPriority":[],"page":0,"size":10,"sort":["registrationDateTime,desc"]}
        )

        media = InputMediaBuffer(buffer=excel_file, filename="data.xlsx")
        await event.message.answer(
            text="Вот твоя таблица:",
            attachments=[media],
        )
        # Тестовый запрос
        # async with AsyncClient() as client:
        #     resp = await client.post(
        #         url="https://prof.mos.ru/back/api/staff/search",
        #         json={
        #             "page":0,
        #             "search":"",
        #             "size":100,
        #             "sort":["fullName,asc"]
        #         },
        #         headers={
        #             'Content-Type': 'application/json', # Говорим серверу, что хотим получить JSON
        #             'Authorization': f"Bearer {token_value_from_redis}", # Передаем токен авторизации
        #             "X-Mes-Subsystem": "proftechw_app"
        #         }
        #     )
            
        # logger.info(f"mosru {resp.status_code}", exc_info=True, extra=resp.json())
        # await event.message.answer(
        #     text=f"{resp.status_code}"
        # )