from time import time
from typing import Sequence
from config import settings
from httpx import AsyncClient


class ECMClient:
    def __init__(self, client: AsyncClient | None = None):
        self._client = client or AsyncClient()

    _token_cache = {
        "access_token": None,
        "expires_at": 0,  # epoch seconds
    }

    async def _get_bearer_token(self, force=False):
        """
        Получение токена OAuth2 (client_credentials) с учетом expires_in.
        """
        now = int(time())
        if (
            not force
            and self._token_cache["access_token"]
            and self._token_cache["expires_at"] - 15 > now
        ):
            return self._token_cache["access_token"]

        data = {
            "grant_type": "client_credentials",
            "client_id": settings.ECM_CLIENT_ID,
            "client_secret": settings.ECM_CLIENT_SECRET,
        }

        resp = await self._client.post(settings.ecm_token_url, data=data)
        token_data = resp.json()

        token = token_data.get("access_token")
        expires_in = int(token_data.get("expires_in", 300))

        self._token_cache["access_token"] = token
        self._token_cache["expires_at"] = now + expires_in
        return token

    async def ecos_change_user_max_id(self, max_id: int, user_id: str):
        url = f"{settings.ecm_records_base}/mutate"
        token = await self._get_bearer_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "records": [
                {"id": f"emodel/person@{user_id}", "attributes": {"max?num": max_id}}
            ],
            "version": 1,
        }

        await self._client.post(url, json=data, headers=headers)

    async def get_user_login_from_ecm(self, max_id: int) -> str:
        url = f"{settings.ecm_records_base}/query"
        token = await self._get_bearer_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "query": {
                "sourceId": "emodel/person",
                "language": "predicate",
                "query": {"t": "eq", "att": "max", "val": max_id},
            },
            "attributes": {"login": "_localId?disp"},
            "version": 1,
        }

        resp = await self._client.post(url, json=data, headers=headers)
        result = resp.json()
        return result["records"][0]["attributes"]["login"]
    
    async def add_records(self, records: Sequence):
        url = f"{settings.ecm_records_base}/mutate"
        token = await self._get_bearer_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "records": records,
            "version": 1,
        }

        resp = await self._client.post(url, json=data, headers=headers)
        result = resp.json()
        return result
    
    async def get_data(self, query: dict):
        url = f"{settings.ecm_records_base}/query"
        token = await self._get_bearer_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        resp = await self._client.post(url, json=query, headers=headers)
        result = resp.json()
        return result


http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)