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
