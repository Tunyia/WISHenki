import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from API.routes import router as api_router
from core.database import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    import models.rating  # noqa: F401 — регистрация моделей в metadata
    import models.activity  # noqa: F401 — регистрация моделей в metadata

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        logger.error(
            "Не удалось подключиться к PostgreSQL. Задайте верный DATABASE_URL "
            "в переменных окружения или в файле .env (см. .env.example в корне проекта). "
            "Для БД в Docker: docker compose up -d и дождитесь готовности контейнера."
        )
        raise
    yield


app = FastAPI(title="Vish Rating API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
