import traceback as tb
import asyncio, os, inspect, uuid
from datetime import datetime, timezone
from contextvars import ContextVar
import aiosqlite
import json
from pathlib import Path

import sys
try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass

def _env_flag(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on", "y")

# ---------- Paths ----------
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent           # utils/ -> project root
DB_PATH = PROJECT_ROOT / "logs" / "logs.db"

# ---------- DB bootstrap ----------
async def init_db():
    """
    Создаёт директории и таблицу логов.
    """
    SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS logs (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    timestamp       INTEGER     NOT NULL,
    level           TEXT        NOT NULL,
    source          TEXT,
    process         TEXT,
    module          TEXT        NOT NULL,
    version         TEXT,
    message         TEXT        NOT NULL,
    traceback       TEXT,
    event_run_id    TEXT,
    context         TEXT
);
"""
    os.makedirs(PROJECT_ROOT / "logs" / "debug", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SQL_CREATE_TABLE)
        await db.commit()

async def write_log_to_db(
    time=None,
    level="none",
    source=None,
    process=None,
    module="none",
    version=None,
    message="none",
    traceback=None,
    event_run_id=None,
    context=None,
):
    """
    Записывает лог в SQLite.
    """
    if time is None:
        time = datetime.now(tz=timezone.utc)
    timestamp = int(time.timestamp() * 1000)

    if isinstance(context, (dict, list)):
        context = json.dumps(context, ensure_ascii=False)

    SQL_WRITE_LOG = """
    INSERT INTO logs
    (timestamp, level, source, process, module, version, message, traceback, event_run_id, context)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            SQL_WRITE_LOG,
            (timestamp, level, source, process, module, version, message, traceback, event_run_id, context),
        )
        await db.commit()

# ---------- Async writer ----------
log_queue = asyncio.Queue()

async def sql_log_writer():
    while True:
        log = await log_queue.get()
        try:
            await write_log_to_db(**log)
        except Exception as e:
            # тут сознательно не используем логгер (чтобы не зациклиться)
            print("[LOG-WRITER ERROR]", e)

async def enqueue_log_entry(**log):
    await log_queue.put(log)

# ---------- Context (event/process) ----------
_EVENT_ID_CTX: ContextVar[str | None] = ContextVar("event_run_id", default=None)
_PROCESS_CTX:  ContextVar[str | None] = ContextVar("process",      default=None)

def begin_event(*, process: str, event_id: str | None = None) -> str:
    """
    Старт логической цепочки: фиксируем process + event_id в contextvars.
    Возвращаем event_id, чтобы при желании протащить в метрики/ответы.
    """
    if event_id is None:
        event_id = str(uuid.uuid4())
    _EVENT_ID_CTX.set(event_id)
    _PROCESS_CTX.set(process)
    return event_id

def set_process(process: str) -> None:
    _PROCESS_CTX.set(process)

def get_current_event_id() -> str | None:
    return _EVENT_ID_CTX.get()

def get_current_process() -> str | None:
    return _PROCESS_CTX.get()

# ---------- Core Logger ----------
class Logger:
    LEVELS = {"CRITICAL": 0, "ERROR": 1, "WARN": 2, "INFO": 3, "DEBUG": 4}

    # цвет по уровню: DEBUG=синий, INFO=зелёный, WARN=жёлтый, ERROR/CRIT=красный
    LEVEL_COLOR = {
        "DEBUG": 34,  # blue
        "INFO": 32,  # green
        "WARN": 33,  # yellow
        "ERROR": 31,  # red
        "CRITICAL": 31,  # red
    }

    def __init__(self, *, source="orion", version="dev", log_level="ERROR", log_to_file=False, use_color=True):
        self.source = source
        self.version = version
        self.log_level = self.get_int_level(log_level)
        self.log_to_file = log_to_file
        disable_color = _env_flag("NO_COLOR", default=False)
        force_color = _env_flag("FORCE_COLOR", default=False)
        self.use_color = (
                use_color
                and not disable_color
                and (force_color or sys.stdout.isatty())
        )

    def get_int_level(self, str_level: str) -> int:
        return self.LEVELS.get(str_level.upper(), 3)

    # sugar
    def DEBUG(self, message, **kw):
        self.log(message, mess_level_in="DEBUG", **kw)

    def INFO(self, message, **kw):
        self.log(message, mess_level_in="INFO", **kw)

    def WARN(self, message, **kw):
        self.log(message, mess_level_in="WARN", **kw)

    def ERROR(self, message, **kw):
        self.log(message, mess_level_in="ERROR", **kw)

    def CRITICAL(self, message, **kw):
        self.log(message, mess_level_in="CRITICAL", **kw)

    def EXCEPTION(self, message: str, exc: Exception, **kw):
        full_message = f"{message}\n→{str(exc)}"
        self.log(full_message, mess_level_in="ERROR", traceback=tb.format_exc(), **kw)

    def log(
        self,
        message="NO LOG MESSAGE",
        *,
        module: str | None = None,
        mess_level_in: str = "INFO",
        traceback: str | None = None,
        color=31,
        style=5,
        context=None,
        event_id: str | None = None,
        source: str | None = None,   # можно переопределить source на вызове (для библиотек)
    ):
        # auto module by caller if not provided
        if module is None:
            frame = inspect.stack()[2]
            module = os.path.basename(frame.filename)

        # dynamic context
        process  = get_current_process()
        event_id = event_id or get_current_event_id()

        # levels
        mess_level = self.get_int_level(mess_level_in)

        # console
        log_time = datetime.now(tz=timezone.utc)
        time_frame = log_time.strftime("[%Y.%m.%d %H:%M:%S:%f]")
        console_line = f"[{mess_level_in}]\t{time_frame} ({module}) {message}"

        if self.log_level >= mess_level:
            if self.use_color:
                color_code = self.LEVEL_COLOR.get(mess_level_in, 37)  # 37 = white
                # только цвет, без "style=5" — это ломает частично-совместимые консоли
                print(f"\033[{color_code}m{console_line}\033[0m")
            else:
                print(console_line)

        # enqueue to DB
        src = source or self.source
        try:
            asyncio.get_running_loop().create_task(
                enqueue_log_entry(
                    time=log_time,
                    level=mess_level_in,
                    source=src,
                    process=process,
                    module=module,
                    version=self.version,
                    message=message,
                    traceback=traceback,
                    event_run_id=event_id,
                    context=context,
                )
            )
        except RuntimeError:
            # если лупа нет — запустим временный
            import threading
            threading.Thread(
                target=lambda: asyncio.run(
                    enqueue_log_entry(
                        time=log_time,
                        level=mess_level_in,
                        source=src,
                        process=process,
                        module=module,
                        version=self.version,
                        message=message,
                        traceback=traceback,
                        event_run_id=event_id,
                        context=context,
                    )
                ),
                daemon=True,
            ).start()

# ---------- Singleton API ----------
_GLOBAL_LOGGER: Logger | None = None

def init_global_logger(*, source="orion", version="dev", log_level="INFO", log_to_file=False) -> Logger:
    """
    Создаёт/возвращает глобальный логгер. Вызывать один раз при старте сервиса.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = Logger(source=source, version=version, log_level=log_level, log_to_file=log_to_file)
    return _GLOBAL_LOGGER

def get_logger(module: str | None = None, source: str | None = None):
    """
    Возвращает фасад для удобных .INFO/.ERROR методов.
    - module: логическое имя модуля (если не указать — возьмётся из stack на каждом вызове)
    - source: переопределение source (например, 'discord', 'sqlalchemy'), иначе возьмётся из core
    """
    if _GLOBAL_LOGGER is None:
        raise RuntimeError("Logger is not initialized. Call init_global_logger() in main.py first.")
    core = _GLOBAL_LOGGER

    class _Facade:
        def _call(self, level, msg, **kw):
            # приоритет явного module/source из вызова > дефолт фасада > авто
            if module is not None and "module" not in kw:
                kw["module"] = module
            if source is not None and "source" not in kw:
                kw["source"] = source
            return core.log(msg, mess_level_in=level, **kw)

        def DEBUG(self, msg, **kw):    return self._call("DEBUG", msg, **kw)
        def INFO(self, msg, **kw):     return self._call("INFO", msg, **kw)
        def WARN(self, msg, **kw):     return self._call("WARN", msg, **kw)
        def ERROR(self, msg, **kw):    return self._call("ERROR", msg, **kw)
        def CRITICAL(self, msg, **kw): return self._call("CRITICAL", msg, **kw)
        def EXCEPTION(self, msg, exc, **kw):
            kw.setdefault("traceback", tb.format_exc())
            return self._call("ERROR", f"{msg}\n→{exc}", **kw)

    return _Facade()

# === stdlib logging → Orion =================================================
import logging
import traceback as _tb

class _OrionLoggingHandler(logging.Handler):
    """
    Прокидывает записи stdlib logging в наш логгер.
    source берём из record.name (или переопределяем параметром конструктора).
    process/event_id — из contextvars (begin_event/set_process).
    """
    def __init__(self, *, default_process_if_none: str | None = "bootstrap", fixed_source: str | None = None):
        super().__init__()
        self.default_process_if_none = default_process_if_none
        self.fixed_source = fixed_source

    def emit(self, record: logging.LogRecord):
        # мапим уровни stdlib → наш текстовый
        if record.levelno >= logging.CRITICAL:
            lvl = "CRITICAL"
        elif record.levelno >= logging.ERROR:
            lvl = "ERROR"
        elif record.levelno >= logging.WARNING:
            lvl = "WARN"
        elif record.levelno >= logging.INFO:
            lvl = "INFO"
        else:
            lvl = "DEBUG"

        msg = record.getMessage()

        tb_text = None
        if record.exc_info:
            tb_text = "".join(_tb.format_exception(*record.exc_info))

        # источник — имя логгера (discord, uvicorn, sqlalchemy, ...)
        src = self.fixed_source or (record.name.split(".")[0] if record.name else "ext")

        # модуль — из record, если есть
        module = record.module or record.filename or "external"

        # берём фасад (а не core) и вызываем соответствующий метод
        try:
            facade = get_logger()
        except Exception:
            # если логгер ещё не инициализирован — не роняем поток логов
            print(f"[orion-log][{lvl}] ({src}|{module}) {msg}")
            if tb_text:
                print(tb_text)
            return

        # если в контексте нет process — подставим дефолт
        if get_current_process() is None and self.default_process_if_none:
            set_process(self.default_process_if_none)

        # дёргаем метод фасада по уровню
        if lvl == "CRITICAL":
            facade.CRITICAL(msg, source=src, module=module, traceback=tb_text, context={"logger": record.name})
        elif lvl == "ERROR":
            facade.ERROR(msg, source=src, module=module, traceback=tb_text, context={"logger": record.name})
        elif lvl == "WARN":
            facade.WARN(msg, source=src, module=module, context={"logger": record.name})
        elif lvl == "INFO":
            facade.INFO(msg, source=src, module=module, context={"logger": record.name})
        else:
            facade.DEBUG(msg, source=src, module=module, context={"logger": record.name})


def hook_std_logging(
    *,
    capture_warnings: bool = True,
    quiet_access: bool = True,
    default_process_if_none: str | None = "bootstrap",
    extra_loggers: dict[str, int] | None = None,
) -> None:
    """
    Подключает наш хэндлер к популярным библиотекам.
    - capture_warnings=True: перенаправить warnings → logging
    - quiet_access=True: притушить 'uvicorn.access'
    - default_process_if_none: если в контексте нет process — подставим (bootstrap)
    - extra_loggers: доп. словарь {'logger.name': LEVEL}
    """
    if capture_warnings:
        logging.captureWarnings(True)

    handler = _OrionLoggingHandler(default_process_if_none=default_process_if_none)

    # базовый набор "шумных" логгеров
    targets: dict[str, int] = {
        "discord": logging.INFO,
        "uvicorn": logging.INFO,
        "uvicorn.error": logging.INFO,
        "uvicorn.access": logging.WARNING if quiet_access else logging.INFO,
        "fastapi": logging.INFO,
        "asyncio": logging.WARNING,
        "watchfiles": logging.WARNING,
        "httpx": logging.WARNING,
        "aiohttp": logging.WARNING,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
    }
    if extra_loggers:
        targets.update(extra_loggers)

    # повесим наш хэндлер на каждый
    for name, level in targets.items():
        lg = logging.getLogger(name)
        lg.setLevel(level)
        # избежать дублей
        if not any(isinstance(h, _OrionLoggingHandler) for h in lg.handlers):
            lg.addHandler(handler)
        # обычно не хотим двойной печати (их консоль + наша)
        lg.propagate = False