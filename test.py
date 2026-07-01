from asyncio import run
from itertools import batched
import os
from pprint import pprint

from httpx import AsyncClient

from bot.mosru.depends import report_process_to_ecm
from utils.ecm import ECMClient


http_client = AsyncClient()
ecm_client = ECMClient(client=http_client)


async def main():
    ...
    # result = await ecm_client.get_user_login_from_ecm(int(input("input max_id: ")))
    # print(result)
    token = os.getenv("TOKEN_TEST")

    # await report_process_to_ecm(token)
    # print(len(data_to_ecm))
    # for applicant in data_to_ecm:
    #     record = await ecm_client.get_data(
    #         query={
    #             "records": ["emodel/admission-committee:itmoscow-statements@54441081222"],
    #             "attributes": [applicant["statement-applicant-name"]],
    #             "version": 1,
    #         }
    #     )
    #     if record['records'][0]['attributes']['statement-applicant-name'] is None:

        
    # # pprint(data_to_ecm[-1])

    # # upload_records = await ecm_client.add_records([data_to_ecm[-1]])
    # # print(upload_records)

    # record = await ecm_client.get_data(
    #     query={
    #         "records": ["emodel/admission-committee:itmoscow-statements@54441081"],
    #         "attributes": ["?json"],
    #         "version": 1,
    #     }
    # )
    # print(record)

    # chunk_size = 100
    # chunks = list(batched(data_to_ecm, chunk_size))
    # for chunk in chunks:
    #     upload_records = await ecm_client.add_records(chunk)

    # df_result.to_excel('merged_output.xlsx', index=False, engine='openpyxl')

    resp = await http_client.post(
        url="https://prof.mos.ru/back/api/applications/search",
        json={
            "learningYearId": 1002678188,
            "rklCheckStatuses": [],
            "applicationPriority": [],
            # "applicantTypes": ["NINE_MSC","NINE_NOT_MSC","ELEVEN"],
            "applicantTypes": ["NINE_NOT_MSC"],
            "page": 0,
            "size": 10000,
            "sort": ["registrationDateTime,desc"],
        },
        headers={
            "Content-Type": "application/json",  # Говорим серверу, что хотим получить JSON
            "Authorization": f"Bearer {token}",  # Передаем токен авторизации
            "X-Mes-Subsystem": "proftechw_app",
        },
    )
    pprint(resp.json())


if __name__ == "__main__":
    run(main())
