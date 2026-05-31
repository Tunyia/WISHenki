# WISHenki — веб-сервис «ВИШенки»

Учёт баллов студентов, рейтинг, мероприятия и регистрация на события.

**Стек:** HTML/CSS/JS (фронт) · FastAPI + PostgreSQL (бэкенд) · Docker Compose

## Быстрый старт (локально)

```powershell
cd путь\к\WISHenki
docker compose up --build
```

Сайт: **http://127.0.0.1:8080**

Демо-данные (один раз):

```powershell
docker compose exec api python seed.py --wait 60
```

---

## Документация проекта

| Файл | О чём |
|------|--------|
| **[DOCKER.md](DOCKER.md)** | Локальный запуск через Docker: сервисы, порты, seed, полезные команды, `list_users.py` |
| **[DEPLOY.md](DEPLOY.md)** | Деплой на VPS: требования к серверу, `.env`, prod-compose, обновления, бэкап, `list_users.py` |
| **[backend/project_vuz/README.md](backend/project_vuz/README.md)** | Бэкенд отдельно: venv, API без полного Docker, seed, переменные окружения |
| **[.env.example](.env.example)** | Шаблон секретов для **prod** (пароли БД, JWT, порт) |
| **[backend/project_vuz/.env.example](backend/project_vuz/.env.example)** | Шаблон для локального API (DATABASE_URL, SECRET_KEY) |
| **`other goods/tech_task/`** | Техническое задание и материалы заказчика (docx, pdf) — не инструкции по запуску |

### Консольные утилиты (в контейнере `api`)

| Скрипт | Назначение |
|--------|------------|
| `seed.py` | Демо-данные: студенты, мероприятия, посещения, вишенки |
| `list_users.py` | Список зарегистрированных аккаунтов (email + студент, **без паролей**) |
| `import_excel.py` | Импорт студентов и бонусных вишенок из Excel (лист 2-го семестра) |
| `admin_menu.py` | Интерактивное CRUD-меню администратора в консоли |

Подробные команды — в [DOCKER.md](DOCKER.md) и [DEPLOY.md](DEPLOY.md).

### Импорт из Excel (2-й семестр)

Файл: `excel_table/2 команда Копия Лидер инженерных школ 2025_2026.xlsx`, лист **2-ой семестр 20252026**.

```powershell
docker compose exec api python import_excel.py --dry-run
docker compose exec api python import_excel.py --force
```

`--force` удаляет текущие данные (студентов, мероприятия, аккаунты) и заливает из таблицы.

### Меню администратора (`admin_menu.py`)

Интерактивное CRUD-меню в консоли (студенты, аккаунты, мероприятия). Подробнее — [DOCKER.md](DOCKER.md#меню-администратора-admin_menupy).

```powershell
docker compose exec -it api python admin_menu.py
```

На VPS: `docker compose -f docker-compose.prod.yml --env-file .env exec -it api python admin_menu.py`

---

## Структура репозитория (кратко)

```text
WISHenki/
├── index.html, app.js, style.css   # фронтенд
├── docker-compose.yml              # локальная разработка
├── docker-compose.prod.yml         # VPS / демо
├── photos/                         # картинки мероприятий
├── backend/project_vuz/            # FastAPI, модели, seed, list_users
├── docker/                         # nginx, Dockerfile для web
└── scripts/                        # deploy.sh, backup-db.sh (VPS)
```
