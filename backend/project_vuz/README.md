# project_vuz

Инструкция запуска (написал **tunya**).

## Что это
Бэкенд на **FastAPI** + **SQLAlchemy** + **PostgreSQL** (БД в Docker).

Фронт лежит в корне репозитория и ходит в API по HTTP.

## Запуск всего проекта одной командой (рекомендуется)

Из **корня репозитория** `WISHenki` (не из этой папки):

```powershell
docker compose up --build
```

Сайт: **http://127.0.0.1:8080** · API: **http://127.0.0.1:8000/health**

Демо-данные: `docker compose exec api python seed.py`

Подробнее: [DOCKER.md](../../DOCKER.md) в корне репозитория. Обзор всей документации: [README.md](../../README.md).

---

## Быстрый старт (только БД в Docker + API/фронт локально)
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

## Просмотр аккаунтов (`list_users.py`)

На сайте нет списка пользователей. Скрипт выводит email, ФИО, группу и вишенки (**пароли не показываются**).

Через Docker (из корня репозитория):

```powershell
docker compose exec api python list_users.py
docker compose exec api python list_users.py --all-students
```

Локально через venv (из `backend/project_vuz`, при работающей БД):

```powershell
.\.venv\Scripts\python list_users.py
.\.venv\Scripts\python list_users.py --all-students
```

`seed.py` создаёт студентов рейтинга **без** логинов — в `list_users.py` только зарегистрировавшиеся на сайте.

## Меню администратора (`admin_menu.py`)

Интерактивное меню с выбором действий по цифрам: просмотр студентов (с аккаунтом и без), запись на мероприятия, посещения, удаление аккаунта или студента, сброс пароля.

**Docker** (из корня репозитория, флаг `-it` обязателен):

```powershell
docker compose exec -it api python admin_menu.py
```

**Локально через venv** (из `backend/project_vuz`, при работающей БД):

```powershell
.\.venv\Scripts\python admin_menu.py
```

Полная инструкция: [DOCKER.md](../../DOCKER.md#меню-администратора-admin_menupy).

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

