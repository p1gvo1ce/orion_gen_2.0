# Orion Gen 2.0

Async agent platform skeleton with Discord bot entrypoint, structured logging, and monitoring via **Gritana** (custom log viewer).

---

## 🚀 Features (Implemented)

- **Async logging system**
  - Global singleton logger
  - Context-bound `event_id` + `process`
  - Automatic `module` detection via `inspect`
  - Async queue + SQLite sink
  - Console output with ANSI colors (INFO=green, WARN=yellow, ERROR/CRIT=red)
  - Capture logs from libraries (`discord`, `uvicorn`, `sqlalchemy`, …)
  - Gritana frontend for viewing/filtering logs (DSL queries)

- **Project entrypoint**
  - `main.py` starts global logger, DB, and background writer
  - Discord bot integration (`discord.py`)
  - `.env` support via `pydantic-settings`

---

## 📌 TODO

- [ ] Add **Telegram** entrypoint (parallel to Discord)
- [ ] Extend **DSL parser** (nested groups, OR precedence, regex on context)
- [ ] Add **Postgres + Alembic** migration layer
- [ ] Write **unit/integration tests**
- [ ] Finalize **agent pipeline** (RAG, retries, fallbacks)

---

## 🛠 Project structure

orion_gen_2.0/
├── gritana/ # frontend + backend for log viewing
│ ├── backend/
│ └── frontend/
├── utils/
│ ├── logger.py # async structured logger
│ └── inspect_logs.py # quick log inspection
├── logs/ # SQLite db + debug logs
├── main.py # entrypoint
├── discord_bot.py # Discord bot integration
├── .env # secrets (Discord token etc.)
└── requirements.txt # dependencies


---

## 🔧 Installation

```bash
# create virtualenv
python -m venv .venv
source .venv/bin/activate   # (Linux/Mac)
.venv\Scripts\activate      # (Windows)

# install dependencies
pip install -r requirements.txt

Generate dependency list:

pip freeze > requirements.txt

🖥 Run

# backend API (FastAPI + Uvicorn)
.venv\Scripts\python.exe -m uvicorn gritana.backend.main:app --reload --port 8000

# frontend (Vite)
cd gritana/frontend/gritana-ui
npm run dev

# open logs UI
http://localhost:5173

📜 License

Internal educational project. Not for production.