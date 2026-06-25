
import io
from typing import Literal

from httpx import AsyncClient


async def download_file_http(url: str, token: str, json: dict, method: Literal["GET", "POST"] = "POST", http_client: AsyncClient = AsyncClient()):
    headers = {"Authorization": f"Bearer {token}"}
    file_buffer = io.BytesIO()

    async with http_client as session:
        async with session.stream(method, url, headers=headers, follow_redirects=True) as response:
            response.raise_for_status()
            
            async for chunk in response.aiter_bytes():
                file_buffer.write(chunk)

    file_buffer.seek(0)
    return file_buffer