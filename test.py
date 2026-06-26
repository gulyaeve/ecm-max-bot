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

    data_to_ecm = await report_process_to_ecm(token)
    print(len(data_to_ecm))
    pprint(data_to_ecm[-1])

    
    upload_records = await ecm_client.add_records([data_to_ecm[-1]])
    print(upload_records)

    # chunk_size = 100
    # chunks = list(batched(data_to_ecm, chunk_size))
    # for chunk in chunks:
    #     upload_records = await ecm_client.add_records(chunk)
    
    # df_result.to_excel('merged_output.xlsx', index=False, engine='openpyxl')


if __name__ == "__main__":
    run(main())
