import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from API.auth_routes import router as auth_router
from API.routes import router as api_router
from core.database import Base, engine
from core.migrate import ensure_schema_updates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    import models.rating  # noqa: F401 — регистрация моделей в metadata
    import models.activity  # noqa: F401 — регистрация моделей в metadata

    try:
        Base.metadata.create_all(bind=engine)
        ensure_schema_updates()
    except OperationalError as e:
        logger.error(
            "Не удалось подключиться к PostgreSQL. Задайте верный DATABASE_URL "
            "в переменных окружения или в файле .env (см. .env.example в корне проекта). "
            "Для БД в Docker: docker compose up -d и дождитесь готовности контейнера."
        )
        raise
    yield


app = FastAPI(title="Vish Rating API", lifespan=lifespan)

# Для учебного проекта разрешены все origin (удобно с Live Server, LAN, file://).
# В продакшене сузьте список доменов.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

# Картинки мероприятий: photos/ в корне репозитория или PHOTOS_DIR (Docker).
_repo_root = Path(__file__).resolve().parent.parent.parent
_photos_dir = Path(os.environ.get("PHOTOS_DIR", str(_repo_root / "photos")))
if _photos_dir.is_dir():
    app.mount(
        "/photos",
        StaticFiles(directory=str(_photos_dir)),
        name="activity_photos",
    )


@app.get("/health")
def health():
    return {"status": "ok"}
