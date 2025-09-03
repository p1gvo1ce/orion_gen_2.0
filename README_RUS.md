# Orion Gen 2.0

Учебный каркас платформы агентов с входной точкой через Discord-бота, структурированным логированием и просмотром логов через **Gritana**.

---

## 🚀 Реализовано

- **Асинхронный логгер**
  - Глобальный синглтон
  - Контекстные `event_id` и `process`
  - Автоопределение `module` через `inspect`
  - Асинхронная очередь + SQLite
  - Цветной вывод в консоль (INFO=зелёный, WARN=жёлтый, ERROR/CRIT=красный)
  - Перехват логов библиотек (`discord`, `uvicorn`, `sqlalchemy`, …)
  - Веб-интерфейс Gritana для просмотра и фильтрации (DSL-запросы)

- **Точка входа**
  - `main.py` — инициализация логгера, базы и фонового воркера
  - Интеграция Discord-бота (`discord.py`)
  - Поддержка `.env` через `pydantic-settings`

---

## 📌 TODO

- [ ] Подключить **Telegram** в качестве второго входа
- [ ] Расширить **DSL-парсер** (вложенные группы, приоритет OR, regex по context)
- [ ] Добавить **Postgres + Alembic** миграции
- [ ] Написать **unit/integration тесты**
- [ ] Финализировать пайплайн агента (RAG, retries, fallbacks)

---

## 🛠 Структура проекта

orion_gen_2.0/
├── gritana/ # фронтенд + бэкенд просмотра логов
│ ├── backend/
│ └── frontend/
├── utils/
│ ├── logger.py # асинхронный структурированный логгер
│ └── inspect_logs.py # быстрый просмотр логов
├── logs/ # база SQLite + отладочные логи
├── main.py # точка входа
├── discord_bot.py # Discord-бот
├── .env # токены и секреты
└── requirements.txt # зависимости


---

## 🔧 Установка

```bash
# создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac

# установить зависимости
pip install -r requirements.txt

Сохранить список зависимостей:

pip freeze > requirements.txt

🖥 Запуск

# бэкенд (FastAPI + Uvicorn)
.venv\Scripts\python.exe -m uvicorn gritana.backend.main:app --reload --port 8000

# фронтенд (Vite)
cd gritana/frontend/gritana-ui
npm run dev

# открыть интерфейс логов
http://localhost:5173

📜 Лицензия

Учебный внутренний проект. Не для продакшена.