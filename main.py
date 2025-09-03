import asyncio
from pydantic_settings import BaseSettings
from utils.logger import (
    init_db, sql_log_writer,
    init_global_logger, get_logger,
    begin_event, set_process,
    hook_std_logging
)
from discord_bot import run_bot as run_discord

class Settings(BaseSettings):
    discord_token: str
    force_color: int
    class Config:
        env_file = ".env"

settings = Settings()

async def main():
    # 0) база + воркер
    await init_db()
    asyncio.create_task(sql_log_writer())

    # 1) глобальный логгер
    init_global_logger(source="orion", version="0.1", log_level="INFO")

    # 2) подключить stdlib logging → наш логгер
    hook_std_logging(quiet_access=True)

    # 3) взять фасад
    log = get_logger(module="main")

    # 4) старт цепочки
    event_id = begin_event(process="main")
    log.INFO("🚀 Orion startup begin", event_id=event_id)

    # старт общей цепочки
    event_id = begin_event(process="main")
    log.INFO("🚀 Orion startup begin", event_id=event_id)

    # таски для разных платформ
    tasks = []
    tasks.append(asyncio.create_task(run_discord( token=settings.discord_token, event_id=event_id)))
    log.DEBUG(msg="Orion Discord startup", event_id=event_id)


    # подождём, пока они все живы
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
