from asyncio import run

from httpx import AsyncClient

from utils.ecm import ECMClient
from utils.http_utils import download_file_http
import pandas as pd


http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)


async def main():
    ...
    # result = await ecm_client.get_user_login_from_ecm(int(input("input max_id: ")))
    # print(result)
    token = ""
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
    #             'Authorization': f"Bearer {token}", # Передаем токен авторизации
    #             "X-Mes-Subsystem": "proftechw_app"
    #         }
    #     )
    async with AsyncClient() as client:
        excel_file = await download_file_http(
            url="https://prof.mos.ru/back/api/applications/report",
            token=token,
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

        resp = await client.post(
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
                "Authorization": f"Bearer {token}",  # Передаем токен авторизации
                "X-Mes-Subsystem": "proftechw_app",
            },
        )

    df_excel = pd.read_excel(excel_file, header=1, dtype=str)

    print(df_excel.head())

    df_json = pd.DataFrame(resp.json()["content"])
    print(df_json.head())

    # excel_key_column = df_excel.columns[6] 
    df_result = pd.merge(
        df_excel, 
        df_json, 
        left_on="Номер", 
        right_on='registrationNumber', 
        how='left' # 'left' сохранит ВСЕ строки из Excel и добавит данные из JSON там, где совпали номера
    )

    df_result.to_excel('merged_output.xlsx', index=False, engine='openpyxl')

    # pprint(resp.json())


if __name__ == "__main__":
    run(main())
