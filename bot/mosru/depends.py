from datetime import datetime
import io
from pathlib import Path
from typing import Optional
import zipfile

import anyio

from utils.redis import redis_client
from utils.http_utils import download_file_http
from logger import logger
from httpx import HTTPStatusError
from config import settings
from utils.max_bot import bot
from utils.ecm import http_client
import pandas as pd


UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(exist_ok=True)


async def create_reports_zip() -> Optional[str]:

    async with redis_client as cache:
        token_value_from_redis = await cache.get("mosru_token")

    try:
        final_zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            final_zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as main_zip:
            for i in range(1, 6):
                excel_file = await download_file_http(
                    url="https://prof.mos.ru/back/api/applications/report",
                    token=token_value_from_redis,
                    json={
                        "learningYearId": 1002678188,
                        "rklCheckStatuses": [],
                        "applicationPriority": [f"{str(i)}"],
                        "page": 0,
                        "size": 10,
                        "sort": ["registrationDateTime,desc"],
                    },
                )

                file_name_in_zip = f"report_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}_priority_{i}.xlsx"
                main_zip.writestr(file_name_in_zip, excel_file.read())

        file_path = UPLOAD_DIR / f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.zip"

        async with await anyio.open_file(file_path, "wb") as out_file:
            await out_file.write(final_zip_buffer.getvalue())

        final_zip_buffer.close()

        return file_path

    except HTTPStatusError as exc:
        if exc.response.status_code == 401:
            logger.warning("Ошибка: Невалидный Bearer токен!")

            await bot.send_message(
                user_id=settings.MAX_ID_TOKEN_HOLDER,
                text="Добрый день! Обновите, пожалуйста, токен.\n\nС наилучшими пожеланиями, ИТ.Москва",
            )

        logger.warning("Ошибка внешнего сервера!")


async def create_report_xlsx() -> str:
    async with redis_client as cache:
        token_value_from_redis = await cache.get("mosru_token")

    excel_file = await download_file_http(
        url="https://prof.mos.ru/back/api/applications/report",
        token=token_value_from_redis,
        json={
            "learningYearId": 1002678188,
            "rklCheckStatuses": [],
            "applicationPriority": [],
            "page": 0,
            "size": 10,
            "sort": ["registrationDateTime,desc"],
        },
        http_client=http_client,
    )

    resp = await http_client.post(
        url="https://prof.mos.ru/back/api/applications/search",
        json={
            "learningYearId": 1002678188,
            "rklCheckStatuses": [],
            "applicationPriority": [],
            "page": 0,
            "size": 1000,
            "sort": ["registrationDateTime,desc"],
        },
        headers={
            "Content-Type": "application/json",  # Говорим серверу, что хотим получить JSON
            "Authorization": f"Bearer {token_value_from_redis}",  # Передаем токен авторизации
            "X-Mes-Subsystem": "proftechw_app",
        },
    )

    df_excel = pd.read_excel(excel_file, header=1, dtype=str)

    # print(df_excel.head())

    df_json = pd.DataFrame(resp.json()["content"])
    # print(df_json.head())

    # excel_key_column = df_excel.columns[6] 
    df_result = pd.merge(
        df_excel, 
        df_json, 
        left_on="Номер", 
        right_on='registrationNumber', 
        how='left' # 'left' сохранит ВСЕ строки из Excel и добавит данные из JSON там, где совпали номера
    )

    file_path = UPLOAD_DIR / f"report_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.xlsx"

    df_result.to_excel(file_path, index=False, engine='openpyxl')
    return file_path
