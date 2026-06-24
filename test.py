from asyncio import run

from httpx import AsyncClient

from utils.ecm import ECMClient


http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)


async def main():
    result = await ecm_client.get_user_login_from_ecm(int(input("input max_id: ")))
    print(result)


if __name__ == "__main__":
    run(main())
