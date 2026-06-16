from time import time
from config import settings
from httpx import AsyncClient


token_cache = {
    "access_token": None,
    "expires_at": 0,  # epoch seconds
}

async def get_bearer_token(force=False):
    """
    Получение токена OAuth2 (client_credentials) с учетом expires_in.
    """
    now = int(time())
    if (not force
        and token_cache["access_token"]
        and token_cache["expires_at"] - 15 > now):  # небольшой запас
        return token_cache["access_token"]

    data = {
        "grant_type": "client_credentials",
        "client_id": settings.ECM_CLIENT_ID,
        "client_secret": settings.ECM_CLIENT_SECRET
    }

    async with AsyncClient() as session:
        resp = await session.post(settings.ecm_token_url, data=data)
        # resp.raise_for_status()
    token_data = resp.json()

    token = token_data.get("access_token")
    expires_in = int(token_data.get("expires_in", 300))

    token_cache["access_token"] = token
    token_cache["expires_at"] = now + expires_in
    return token


async def ecos_change_user_max_id(max_id: int, user_id: str):
    url = f"{settings.ecm_records_base}/mutate"
    token = await get_bearer_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "records": [
            {
                "id": f"emodel/person@{user_id}",
                "attributes": {
                    "max?num": max_id
                }
            }
        ],
        "version": 1
    }

    async with AsyncClient(headers=headers) as session:
        await session.post(url, json=data)


