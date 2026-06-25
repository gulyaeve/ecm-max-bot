from asyncio import run

from httpx import AsyncClient

from utils.ecm import ECMClient


http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)


async def main():
    ...
    # result = await ecm_client.get_user_login_from_ecm(int(input("input max_id: ")))
    # print(result)
    token_value_from_redis = ""
    async with AsyncClient() as client:
        resp = await client.post(
            url="https://prof.mos.ru/back/api/staff/search",
            json={
                "page":0,
                "search":"",
                "size":100,
                "sort":["fullName,asc"]
            },
            headers={
                'Content-Type': 'application/json', # Говорим серверу, что хотим получить JSON
                'Authorization': f"Bearer {token_value_from_redis}", # Передаем токен авторизации
                "X-Mes-Subsystem": "proftechw_app"
            }
        )
            
    print(f"mosru {resp.status_code} {resp.json()}")


if __name__ == "__main__":
    run(main())
