from typing import List, Optional
import asyncio
from fastapi import APIRouter, Query
import aiosqlite, re, time
from pathlib import Path
from gritana.backend.services.dsl_parser import parse_dsl

router = APIRouter(prefix="/ritual/logs", tags=["ritual"])

# Путь не тот, что ты видишь — путь тот, что исполняется.
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent

DB_PATH = PROJECT_ROOT / "logs" / "logs.db"
print(DB_PATH)

async def db_check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM logs")
        count = await cursor.fetchone()
        print("→ Количество строк в logs:", count["cnt"])

#asyncio.run(db_check())

@router.get("/")
async def get_logs(
        level: Optional[str] = None,
        source: Optional[str] = None,
        process: Optional[str] = None,
        module: Optional[str] = None,
        version: Optional[str] = None,
        event_run_id: Optional[str] = None,
        limit: int = 1000
):
    query = "SELECT * FROM logs WHERE 1=1"
    params = []

    if level:
        query += " AND level = ?"
        params.append(level)
    if source:
        query += " AND source = ?"
        params.append(source)
    if process:
        query += " AND process = ?"
        params.append(process)
    if module:
        query += " AND module = ?"
        params.append(module)
    if version:
        query += " AND version = ?"
        params.append(version)
    if event_run_id:
        query += " AND event_run_id = ?"
        params.append(event_run_id)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        logs = await cursor.fetchall()

    return [dict(row) for row in logs]

@router.get("/levels")
async def get_levels():
    return ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]

@router.get("/modules")
async def get_modules():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        curor = await db.execute("SELECT DISTINCT module FROM logs ORDER BY module")
        rows = await curor.fetchall()
        return [row["module"] for row in rows]

@router.get("/sources")
async def get_sources():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT DISTINCT source FROM logs ORDER BY source")
        rows = await cursor.fetchall()
        return [row["source"] for row in rows if row["source"]]

@router.get("/processes")
async def get_processes():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT DISTINCT process FROM logs ORDER BY process")
        rows = await cursor.fetchall()
        return [row["process"] for row in rows if row["process"]]

@router.get("/versions")
async def get_versions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT DISTINCT version FROM logs ORDER BY version")
        rows = await cursor.fetchall()
        return [row["version"] for row in rows if row["version"]]

@router.get("/stats")
async def get_stats():
    query = """
    SELECT
        strftime('%Y-%m-%d %H:00', timestamp / 1000, 'unixepoch') as hour,
        COUNT(*) as count
    FROM logs
    GROUP BY hour
    ORDER BY hour DESC
    LIMIT 1000
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@router.get("/event_run_ids")
async def get_event_run_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT DISTINCT event_run_id FROM logs ORDER BY event_run_id DESC LIMIT 100")
        rows = await cursor.fetchall()
        return [row["event_run_id"] for row in rows if row["event_run_id"]]


@router.get("/dsl")
async def get_logs_dsl(q: str):
    where_clause, params, message_regex = parse_dsl(q)

    query = "SELECT * FROM logs"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += " ORDER BY timestamp DESC LIMIT 1000"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    # Если есть message_regex, да будут забыты еретические логи
    if message_regex is not None:
        pattern = re.compile(message_regex)
        filtered = [dict(r) for r in rows if pattern.search(r["message"] or "")]
        return filtered
    else:
        return [dict(r) for r in rows]