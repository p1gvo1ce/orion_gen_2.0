import asyncio
from pydantic_settings import BaseSettings
from utils.logger import (
    init_db, sql_log_writer,
    init_global_logger, get_logger,
    begin_event, set_process,
    hook_std_logging
)
from discord_bot import run_bot

class Settings(BaseSettings):
    discord_token: str
    force_color: int
    class Config:
        env_file = ".env"

settings = Settings()

async def main():
    # 0) база + фоновый воркер логов
    await init_db()
    asyncio.create_task(sql_log_writer())

    # 1) глобальный логгер
    init_global_logger(source="orion", version="0.1", log_level="INFO")
    hook_std_logging(quiet_access=True)
    log = get_logger(module="main")

    # 2) старт общей цепочки запуска сервиса
    event_id = begin_event(process="main")
    log.INFO("🚀 Orion startup begin", event_id=event_id)

    try:
        # 3) этап «инициализация дискорда» — тот же event_id, другой process
        set_process("discord_bootstrap")
        log.INFO("🤖 Discord bot init...", event_id=event_id)

        await run_bot(token=settings.discord_token)  # внутри доступен текущий контекст

        # 4) вернёмся в 'main' и финализируем
        set_process("main")
        log.INFO("✅ Orion startup success", event_id=event_id)
    except Exception as e:
        log.EXCEPTION("❌ Orion startup failed", e, event_id=event_id)

if __name__ == "__main__":
    asyncio.run(main())
