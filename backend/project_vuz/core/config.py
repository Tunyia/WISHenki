import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

# По умолчанию — PostgreSQL из docker-compose.yml (порт 5433 на хосте, см. compose).
_DEFAULT_DOCKER_DEV_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5433/vish_rating"
)

DATABASE_URL = os.environ.get("DATABASE_URL") or _DEFAULT_DOCKER_DEV_URL

SQL_ECHO = os.environ.get("SQL_ECHO", "false").lower() in ("1", "true", "yes")

# JWT (для разработки можно не задавать — подставится несекретный ключ из дефолта)
SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 суток

# Группы, разрешённые при регистрации (как на фронте)
ALLOWED_STUDY_GROUPS = frozenset({"ШЦТ-111", "ШЦТ-112", "ГЛЭК-111"})
