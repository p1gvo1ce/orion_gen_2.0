import re
import datetime


def parse_dsl(dsl_string: str):
    """
    Превращает строку-заклинание в SQL-запрос, понятный машине.

    🕯 Поддерживаемые обряды:
        - AND / OR / NOT — логические связки для построения цепей проклятий
        - level, module, source, process, version, event_run_id, message, timestamp — допустимые поля вызова
        - message — интерпретируется как регулярное выражение, ибо текст — это тень смысла
        - timestamp — принимает знаки: >, <, >=, <=, ибо время — не линейно, но поддаётся сравнению

    📜 Примеры DSL-заклинаний:
        level:ERROR AND message:"fail.*int"
        source:discord AND process:discord_bot
        version:0.1 AND event_run_id:b66a4be0-19d1-4eab-899d-9f474495fda3
        NOT module:ai/logic.py AND timestamp:>2025-04-01T00:00:00

    Возвращает:
        - where_clause (str) — часть SQL-запроса для обряда фильтрации
        - params (list) — переменные для подстановки, дабы не тревожить богов инъекциями
        - message_regex (str|None) — регулярка для фильтрации сообщений
    """

    dsl_string = dsl_string.replace("&&", "AND")
    dsl_string = dsl_string.replace("||", "OR")

    tokens = re.split(r'\s+(AND|OR|NOT)\s+', dsl_string.strip())
    sql_parts = []
    params = []
    message_regex = None

    for token in tokens:
        token = token.strip()
        if token in {"AND", "OR", "NOT"}:
            sql_parts.append(token)
            continue

        match = re.match(r'(\w+):([<>]=?|=)?(.*)', token)
        if not match:
            continue

        field, op, value = match.groups()
        field = field.strip()
        op = op.strip() if op else '='
        value = value.strip().strip('"')

        if field == "timestamp":
            try:
                dt = datetime.datetime.fromisoformat(value)
                timestamp = int(dt.timestamp() * 1000)
                sql_parts.append(f"timestamp {op} ?")
                params.append(timestamp)
            except ValueError:
                continue

        elif field == "message":
            # message фильтруется регуляркой, а не SQL
            message_regex = value
            continue

        elif field in {"level", "module", "source", "process", "version", "event_run_id"}:
            sql_parts.append(f"{field} {op} ?")
            params.append(value)

        elif field == "context":
            # context хранится как JSON-строка → LIKE '%value%'
            sql_parts.append("context LIKE ?")
            params.append(f"%{value}%")

    while sql_parts and sql_parts[-1] in {"AND", "OR", "NOT"}:
        sql_parts.pop()

    while sql_parts and sql_parts[0] in {"AND", "OR"}:
        sql_parts.pop(0)

    where_clause = " ".join(sql_parts)
    return where_clause, params, message_regex
