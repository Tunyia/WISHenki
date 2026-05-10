# project_vuz

Инструкция запуска (написал **tunya**).

## Что это
Бэкенд на **FastAPI** + **SQLAlchemy** + **PostgreSQL** (БД в Docker).

Фронт лежит в корне репозитория и ходит в API по HTTP.

## Быстрый старт (Windows / PowerShell)
### 1) Поднять базу данных (Postgres) в Docker
Из папки `backend/project_vuz`:

```powershell
docker compose -f "Docker-compose.yml" up -d
docker compose -f "Docker-compose.yml" ps
```

По умолчанию Postgres будет доступен на хосте: `localhost:5433` (внутри контейнера это `5432`).

### 2) Создать venv и поставить зависимости

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 3) Запустить API

```powershell
.\.venv\Scripts\python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Проверка:

- `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`

## Демо-данные (seed)
`seed.py` умеет сам:
- ждать готовность БД
- создавать таблицы (если их ещё нет)

### Заполнить БД демо-данными (без дублей)

```powershell
.\.venv\Scripts\python seed.py
```

### Полный пересид (очистить таблицы и залить заново)

```powershell
.\.venv\Scripts\python seed.py --force
```

### Если Postgres долго стартует

```powershell
.\.venv\Scripts\python seed.py --force --wait 60
```

## Как “очистить БД и заполнить заново” (полный сброс через Docker volume)
Проще всего удалить Docker volume с данными Postgres (это полностью сбросит БД):

```powershell
docker compose -f "Docker-compose.yml" down -v
docker compose -f "Docker-compose.yml" up -d
.\.venv\Scripts\python seed.py --force --wait 60
```

## Переменные окружения
Можно создать файл `.env` рядом с `main.py` (пример в `.env.example`) и переопределить подключение:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/vish_rating`

