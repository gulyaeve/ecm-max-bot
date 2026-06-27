from asyncio import run
from typing import Literal, Optional

from bot.mosru.depends import report_process_to_ecm


def sync_ecm_report(
    token: str,
    max_id_report: Optional[int] = None,
    mode: Literal["sync", "add_new"] = "sync",
):
    # Запускаем асинхронную функцию внутри отдельного процесса
    return run(report_process_to_ecm(token, max_id_report, mode))
