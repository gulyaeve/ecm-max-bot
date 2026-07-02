import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import anyio
import pandas as pd
from httpx import HTTPStatusError

from config import settings
from logger import logger
from utils.ecm import ecm_client, http_client
from utils.http_utils import download_file_http
from utils.max_bot import bot
from asyncio import Semaphore, gather


UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(exist_ok=True)


async def create_reports_zip(token: str) -> Optional[str]:
    try:
        final_zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            final_zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as main_zip:
            for i in range(1, 6):
                excel_file = await download_file_http(
                    url="https://prof.mos.ru/back/api/applications/report",
                    token=token,
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


async def create_report_xlsx(token: str) -> str:
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

    # resp = await http_client.post(
    #     url="https://prof.mos.ru/back/api/applications/search",
    #     json={
    #         "learningYearId": 1002678188,
    #         "rklCheckStatuses": [],
    #         "applicationPriority": [],
    #         "page": 0,
    #         "size": 1000,
    #         "sort": ["registrationDateTime,desc"],
    #     },
    #     headers={
    #         "Content-Type": "application/json",  # Говорим серверу, что хотим получить JSON
    #         "Authorization": f"Bearer {token}",  # Передаем токен авторизации
    #         "X-Mes-Subsystem": "proftechw_app",
    #     },
    # )

    df_excel = pd.read_excel(excel_file, header=1, dtype=str)

    # print(df_excel.head())

    dfs_json = []
    for applicant_type in ["NINE_MSC", "NINE_NOT_MSC", "ELEVEN"]:
        resp = await http_client.post(
            url="https://prof.mos.ru/back/api/applications/search",
            json={
                "learningYearId": 1002678188,
                "rklCheckStatuses": [],
                "applicationPriority": [],
                "applicantTypes": [applicant_type],
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
        applicants = resp.json()["content"]
        for applicant in applicants:
            applicant["applicantType"] = applicant_type
        df_resp = pd.DataFrame(applicants)
        dfs_json.append(df_resp)
    

    df_json = pd.concat(dfs_json)

    # df_json = pd.DataFrame(resp.json()["content"])
    # print(df_json.head())

    # excel_key_column = df_excel.columns[6]
    df_result = pd.merge(
        df_excel,
        df_json,
        left_on="Номер",
        right_on="registrationNumber",
        how="left",  # 'left' сохранит ВСЕ строки из Excel и добавит данные из JSON там, где совпали номера
    )

    file_path = (
        UPLOAD_DIR / f"report_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.xlsx"
    )

    df_result.to_excel(file_path, index=False, engine="openpyxl")
    return file_path


async def applicant_worker(semaphore, row, mode, counters, types_options):

    statement_status_options = types_options["statement_status_options"]
    statement_type_options = types_options["statement_type_options"]
    statement_verifi_options = types_options["statement_verifi_options"]
    statement_sorce_options = types_options["statement_sorce_options"]
    statement_applicant_sex_options = types_options["statement_applicant_sex_options"]
    statement_education_form_options = types_options["statement_education_form_options"]
    statement_financing_options = types_options["statement_financing_options"]
    statement_document_achivments_options = types_options["statement_document_achivments_options"]
    statement_approval_options = types_options["statement_approval_options"]
    statement_entrance_test_options = types_options["statement_entrance_test_options"]
    statement_state_exam_type = types_options["statement_state_exam_type"]
    statement_priority_admission_options = types_options["statement_priority_admission_options"]
    specs = types_options["specs"]
    doc_types = types_options["doc_types"]

    async with semaphore:
        record = await ecm_client.get_data(
            query={
                "records": [
                    f"emodel/admission-committee:itmoscow-statements@{row['id']}"
                ],
                "attributes": ["statement-applicant-name"],
                "version": 1,
            }
        )
        if record["records"][0]["attributes"]["statement-applicant-name"] is None:
            ecm_id = "emodel/admission-committee:itmoscow-statements@"
        else:
            ecm_id = f"emodel/admission-committee:itmoscow-statements@{row['id']}"
        application = {
            # "id": f"emodel/admission-committee:itmoscow-statements@{row['id']}",
            # "id": "emodel/admission-committee:itmoscow-statements@",
            "id": ecm_id,
            "attributes": {
                "statement-type": f"{statement_type_options.get(row['Тип'], '0')}",
                "statement-status": f"{statement_status_options.get(row['Статус'], '0')}",
                "statement-comment-mcrpo": f"{row['Примечание от МЦРПО'] if pd.notna(row['Примечание от МЦРПО']) else ''}",
                "statement-sorce": f"{statement_sorce_options.get(row['Источник'], '0')}",
                "statement-verifi": f"{statement_verifi_options.get(row['Межвед. проверки'], '1')}",
                "statement-status-change-date": datetime.strptime(
                    row["Изменение статуса"], "%d.%m.%Y"
                ).strftime("%Y-%m-%d"),
                "statement-number": f"{row['Номер']}",
                "statement-registration-date": datetime.strptime(
                    row["Зарегистрирован"], "%d.%m.%Y %H:%M:%S"
                ).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                "statement-applicant-name": f"{row['ФИО']}",
                "statement-applicant-sex": f"{statement_applicant_sex_options.get(row['Пол'])}",
                "statement-applicant-citizenship": f"{row['Гражданство'] if pd.notna(row['Гражданство']) else ''}",
                "statement-applicant-passport-type": f"{row['Тип документа, удостоверяющего личность'] if pd.notna(row['Тип документа, удостоверяющего личность']) else ''}",
                "statement-applicant-passport-series": f"{row['Серия ДУЛ'] if pd.notna(row['Серия ДУЛ']) else ''}",
                "statement-applicant-passport-number": f"{row['Номер ДУЛ'] if pd.notna(row['Номер ДУЛ']) else ''}",
                "statement-applicant-passport-issued": f"{row['Кем выдан ДУЛ'] if pd.notna(row['Кем выдан ДУЛ']) else ''}",
                "statement-applicant-passport-issued-date1": datetime.strptime(
                    row["Дата выдачи ДУЛ"], "%d.%m.%Y"
                ).strftime("%Y-%m-%d")
                if pd.notna(row["Дата выдачи ДУЛ"])
                else None,
                "statement-applicant-passport-issued-code": f"{row['Код подразделения ДУЛ'] if pd.notna(row['Код подразделения ДУЛ']) else ''}",
                "statement-specialization": f"{specs.get(row['Специальность'], '')}",
                "statement-education-form": f"{statement_education_form_options.get(row['Форма обучения'], '0')}",
                "statement-financing": f"{statement_financing_options.get(row['Финансирование'], '0')}",
                "statement-document-achivments": f"{statement_document_achivments_options.get(row['Документ о достижениях'], '0')}",
                "statement-approval": f"{statement_approval_options.get(row['Согласие на зачисление'], '0')}",
                "statement-entrance-test": f"{statement_entrance_test_options.get(row['Вступительные испытания'], '0')}",
                "statement-reason-archiv": f"{row['Причина архивации'] if pd.notna(row['Причина архивации']) else ''}",
                "statement-education-document-type": f"{doc_types.get(row['Тип документа об образовании'], '')}",
                "statement-education-document-series": f"{row['Серия документа об образовании'] if pd.notna(row['Серия документа об образовании']) else ''}",
                "statement-education-document-number": f"{row['Номер документа об образовании'] if pd.notna(row['Номер документа об образовании']) else ''}",
                "statement-education-document-issued": f"{row['Организация, выдавшая документ об образовании (школа)'] if pd.notna(row['Организация, выдавшая документ об образовании (школа)']) else ''}",
                "statement-education-document-issued-date1": datetime.strptime(
                    row["Дата выдачи документа об образовании"], "%d.%m.%Y"
                ).strftime("%Y-%m-%d")
                if pd.notna(row["Дата выдачи документа об образовании"])
                else None,
                "statement-education-document-issued-place": f"{row['Место выдачи аттестата'] if pd.notna(row['Место выдачи аттестата']) else ''}",
                "statement-applicant-phone": f"{row['Контактный телефон'] if pd.notna(row['Контактный телефон']) else ''}",
                "statement-applicant-email": f"{row['Электронная почта'] if pd.notna(row['Электронная почта']) else ''}",
                "statement-applicant-snils": f"{row['СНИЛС'] if pd.notna(row['СНИЛС']) else ''}",
                "statement-applicant-registration-type": f"{row['Тип регистрации'] if pd.notna(row['Тип регистрации']) else ''}",
                "statement-applicant-datebirth": datetime.strptime(
                    row["Дата рождения"], "%d.%m.%Y"
                ).strftime("%Y-%m-%d")
                if pd.notna(row["Дата рождения"])
                else None,
                "statement-applicant-registration-country": f"{row['Место регистрации'] if pd.notna(row['Место регистрации']) else ''}",
                "statement-applicant-registration-adress-full": f"{row['Полный адрес'] if pd.notna(row['Полный адрес']) else ''}",
                "statement-applicant-registration-place": f"{row['Место регистрации'] if pd.notna(row['Место регистрации']) else ''}",
                "statement-applicant-registration-city": f"{row['Населенный пункт/город'] if pd.notna(row['Населенный пункт/город']) else ''}",
                "statement-applicant-registration-region": f"{row['Регион'] if pd.notna(row['Регион']) else ''}",
                "statement-applicant-registration-street": f"{row['Улица'] if pd.notna(row['Улица']) else ''}",
                "statement-applicant-registration-district": f"{row['Район'] if pd.notna(row['Район']) else ''}",
                "statement-applicant-registration-house": f"{row['Дом, строение, корпус'] if pd.notna(row['Дом, строение, корпус']) else ''}",
                "statement-applicant-registration-apartament": f"{row['Квартира'] if pd.notna(row['Квартира']) else ''}",
                "statement-graduation-year": f"{row['Год окончания'] if pd.notna(row['Год окончания']) else ''}",
                "statement-primary-points": row["Сумма первичных баллов"]
                if pd.notna(row["Сумма первичных баллов"])
                else None,
                "statement-average-score": row["Средний балл ГИА"]
                if pd.notna(row["Средний балл ГИА"])
                else None,
                "statement-state-exam-type": f"{statement_state_exam_type.get(row['Тип ГИА'], '0')}",
                "statement-state-exam-count": row["Количество предметов ГИА"]
                if pd.notna(row["Количество предметов ГИА"])
                else None,
                "statement-priority-admission": f"{statement_priority_admission_options.get(row['Приоритетное право'], '0')}",
                "statement-priority-admission-category": f"{row['Категория'] if pd.notna(row['Категория']) else ''}",
                "statement-priority-num": f"{row['applicationPriority'] if pd.notna(row['applicationPriority']) else ''}",
                "statement-proftech-id": f"{row['id']}",
                "statement-proftech-applicantTypes": f"{row['applicantType']}",
                "_alias?str": f"emodel/admission-committee:itmoscow-statements@{row['id']}",
                "_state?str": "submitted",
                "_workspace": "admission-committee",
            },
        }
        try:
            if (
                mode == "add_new"
                and ecm_id == "emodel/admission-committee:itmoscow-statements@"
            ):
                # await sleep(0.2)
                await ecm_client.add_records([application])
                counters["added_new"] += 1

            elif mode == "sync":
                # await sleep(0.2)
                await ecm_client.add_records([application])
                if ecm_id == "emodel/admission-committee:itmoscow-statements@":
                    counters["added_new"] += 1
                else:
                    counters["updated"] += 1
        except Exception as e:
            logger.warning(f"failed {row['id']} {e}")
            counters["errors"] += 1


async def report_process_to_ecm(
    token: str,
    max_id_report: Optional[int] = None,
    mode: Literal["sync", "add_new"] = "sync",
):
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

    df_excel = pd.read_excel(excel_file, header=1, dtype=str)


    dfs_json = []
    for applicant_type in ["NINE_MSC", "NINE_NOT_MSC", "ELEVEN"]:
        resp = await http_client.post(
            url="https://prof.mos.ru/back/api/applications/search",
            json={
                "learningYearId": 1002678188,
                "rklCheckStatuses": [],
                "applicationPriority": [],
                "applicantTypes": [applicant_type],
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
        applicants = resp.json()["content"]
        for applicant in applicants:
            applicant["applicantType"] = applicant_type
        df_resp = pd.DataFrame(applicants)
        dfs_json.append(df_resp)

    df_json = pd.concat(dfs_json)

    # print(df_excel.head())
    # print(df_json.head())

    df_result = pd.merge(
        df_excel,
        df_json,
        left_on="Номер",
        right_on="registrationNumber",
        how="left",  # 'left' сохранит ВСЕ строки из Excel и добавит данные из JSON там, где совпали номера
    )
    df_result["id"] = df_result["id"].fillna(0)
    df_result["id"] = df_result["id"].astype("Int64")

    statement_type_options = {
        "Восстановление": "1",
        "Направление на зачисление": "2",
        "Перевод": "3",
        "Прием": "4",
        "Продление академического отпуска": "5",
        "Смена типа финансирования": "6",
        "Другое": "0",
    }

    statement_status_options = {
        "Принято": "1",
        "Издан приказ": "2",
        "Зачислен": "3",
        "В архиве": "4",
        "Другое": "0",
        "Ожидает подтверждения": "5",
        "На рассмотрении": "6",
        "Рекомендован к зачислению": "7",
        "На утверждении к рекомендации": "8",
        "Утвержден к рекомендации": "9",
        "Не утвержден к рекомендации": "10",
    }

    statement_sorce_options = {
        "Оператор ПОО": "1",
        "Оператор МЦРПО": "2",
        "МПГУ": "3",
        "Другое": "0",
    }
    statement_verifi_options = {
        "не проверено": "1",
        "подтверждено": "2",
    }
    statement_applicant_sex_options = {
        "Женский": "0",
        "Мужской": "1",
    }
    statement_education_form_options = {
        "Очная": "0",
        "Очно-заочная": "1",
        "Заочная": "2",
    }
    statement_financing_options = {
        "Бюджет": "0",
        "Договор": "1",
    }
    statement_document_achivments_options = {
        "Документов нет": "0",
        "Приложен, но не подтвержден": "1",
        "Приложен и подтвержден": "2",
    }
    statement_approval_options = {
        "Не подписано": "0",
        "Подписано": "1",
    }
    statement_entrance_test_options = {
        "Отсутствуют": "1",
        "Другое": "0",
    }
    statement_state_exam_type = {
        "ОГЭ": "1",
        "ГВЭ": "2",
        "Другое": "0",
    }
    statement_priority_admission_options = {
        "Первоочередное право": "1",
        "Преимущественное право": "2",
        "Первоочередное и преимущественное": "3",
        "Без приоритета": "0",
    }

    specs = dict()
    specs_from_ecm = await ecm_client.get_data(
        query={
            "query": {
                "sourceId": "emodel/itmoscow-specialties",
                "language": "predicate",
                "consistency": "EVENTUAL",
                "query": {
                    "t": "eq",
                    "att": "_type",
                    "val": "emodel/type@itmoscow-specialties",
                },
                "page": {"skipCount": 0, "maxItems": 35, "page": 1},
                "sortBy": [{"attribute": "_created", "ascending": False}],
                "workspaces": ["data-lists-workspace"],
            },
            "attributes": {
                "name": "speciality?disp",
            },
            "version": 1,
        }
    )
    for spec in specs_from_ecm["records"]:
        specs[spec["attributes"]["name"]] = spec["id"]
    # print(specs)

    doc_types = dict()
    doc_types_from_ecm = await ecm_client.get_data(
        query={
            "query": {
                "sourceId": "emodel/admission-committee:itmoscow-educa-f25jq54",
                "language": "predicate",
                "consistency": "EVENTUAL",
                "query": {
                    "t": "eq",
                    "att": "_type",
                    "val": "emodel/type@admission-committee:itmoscow-education-document-list",
                },
                "page": {"skipCount": 0, "maxItems": 35, "page": 1},
                "sortBy": [{"attribute": "_created", "ascending": False}],
                "workspaces": ["admission-committee"],
            },
            "attributes": {
                "name": "title?disp",
            },
            "version": 1,
        }
    )
    for doc_type in doc_types_from_ecm["records"]:
        doc_types[doc_type["attributes"]["name"]] = doc_type["id"]


    types_options = {
        "statement_type_options": statement_type_options,
        "statement_status_options": statement_status_options,
        "statement_sorce_options": statement_sorce_options,
        "statement_verifi_options": statement_verifi_options,
        "statement_applicant_sex_options": statement_applicant_sex_options,
        "statement_education_form_options": statement_education_form_options,
        "statement_financing_options": statement_financing_options,
        "statement_document_achivments_options": statement_document_achivments_options,
        "statement_approval_options": statement_approval_options,
        "statement_entrance_test_options": statement_entrance_test_options,
        "statement_state_exam_type": statement_state_exam_type,
        "statement_priority_admission_options": statement_priority_admission_options,
        "specs": specs,
        "doc_types": doc_types
    }

   
    counters = {"added_new": 0, "updated": 0, "errors": 0}
    tasks = []
    semaphore = Semaphore(100)

    for index, row in df_result.iterrows():
        if row["id"] != 0:
            tasks.append(applicant_worker(semaphore, row, mode, counters, types_options))

    await gather(*tasks)

    if max_id_report is not None:
        report_message = f"Завершено\nОбновлено: {counters['updated']}\nДобавлено: {counters['added_new']}\n"
        if counters.get("errors") != 0:
            report_message += f"Ошибок: {counters['errors']}\n"
        await bot.send_message(
            user_id=max_id_report,
            text=report_message,
        )
    # return data_to_ecm
