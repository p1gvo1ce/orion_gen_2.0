from fastapi import FastAPI
from pathlib import Path
from gritana.backend.api.logs import router as logs_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Путь не тот, что ты видишь — путь тот, что исполняется.
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent

DB_PATH = PROJECT_ROOT / "logs" / "logs.db"

app.include_router(logs_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)