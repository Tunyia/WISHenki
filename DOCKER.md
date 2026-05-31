# Запуск проекта в Docker (локально)

Один файл **`docker-compose.yml`** в корне репозитория поднимает три сервиса:

| Сервис | Что это | Порт на вашем ПК |
|--------|---------|------------------|
| **db** | PostgreSQL — база данных | внутри сети Docker (снаружи не обязателен) |
| **api** | FastAPI — бэкенд, таблицы, `/api/...` | [http://127.0.0.1:8000](http://127.0.0.1:8000) (для отладки) |
| **web** | Nginx — статика сайта + прокси на API | [http://127.0.0.1:8080](http://127.0.0.1:8080) — **открывайте сайт здесь** |

## Что такое Docker Compose

**Docker** запускает приложения в изолированных **контейнерах** (как лёгкие виртуальные машины с одной программой).

**Docker Compose** — описание нескольких контейнеров в одном YAML-файле: как они связаны, какие порты открыть, кто ждёт кого при старте. Команда **`docker compose up`** читает этот файл и поднимает всё сразу.

Схема:

```text
Браузер → http://localhost:8080  (контейнер web, nginx)
              ├─ /, app.js, style.css  — отдаёт nginx с диска
              └─ /api/..., /photos/... — nginx проксирует в контейнер api:8000
                        └─ api пишет/читает PostgreSQL (контейнер db)
```

Фронтенд ходит в API по **относительным** путям (`/api/...`), потому что nginx на том же хосте проксирует запросы — отдельно поднимать `python -m http.server` не нужно.

## Требования

- Установлены [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows) или Docker Engine + Compose plugin.
- Терминал открыт в **корне репозитория** `WISHenki` (где лежит `docker-compose.yml`).

## Первый запуск

```powershell
cd путь\к\WISHenki
docker compose up --build
```

- **`up`** — создать и запустить контейнеры.
- **`--build`** — пересобрать образы api и web (нужно после изменений в коде).

Дождитесь строк вроде `api` / `Application startup complete`, откройте в браузере:

**http://127.0.0.1:8080**

Проверка API напрямую: **http://127.0.0.1:8000/health** → `{"status":"ok"}`.

Остановить: `Ctrl+C` в том же терминале, либо в другом окне:

```powershell
docker compose down
```

Запуск в фоне (терминал свободен):

```powershell
docker compose up --build -d
docker compose logs -f
docker compose down
```

> **Важно:** после изменений в `index.html`, `app.js`, `style.css` нужен `docker compose up -d --build web`.  
> После изменений в бэкенде или скриптах (`seed.py`, `list_users.py`) — `docker compose up -d --build api`.

## Демо-данные (студенты, мероприятия)

После первого `up` таблицы создаются автоматически, но **данные** нужно залить один раз:

```powershell
docker compose exec api python seed.py --wait 60
```

Полный сброс и перезаливка:

```powershell
docker compose down -v
docker compose up --build -d
docker compose exec api python seed.py --force --wait 60
```

`seed.py` создаёт **студентов в рейтинге** и мероприятия, но **не** логины (email/пароль). Аккаунты появляются только после регистрации на сайте.

## Просмотр зарегистрированных аккаунтов (`list_users.py`)

На сайте и в API **нет** админ-страницы со списком пользователей. Для отладки используйте консольный скрипт — он показывает email, ФИО, группу и вишенки. **Пароли не выводятся** (в БД хранятся только хеши).

Если скрипт только что добавлен или обновлён — пересоберите API:

```powershell
docker compose build api
docker compose up -d --force-recreate api
```

**Список аккаунтов** (только те, кто зарегистрировался на сайте):

```powershell
docker compose exec api python list_users.py
```

**Все студенты рейтинга** (включая записи без входа по почте):

```powershell
docker compose exec api python list_users.py --all-students
```

## Импорт из Excel (2-й семестр)

Файл: `excel_table/2 команда Копия Лидер инженерных школ 2025_2026.xlsx`, лист **2-ой семестр 20252026**.

```powershell
docker compose exec api python import_excel.py --dry-run
docker compose exec api python import_excel.py --force
```

`--force` очищает students, activities, users и заливает данные из таблицы.  
981 уникальный студент (31 дубль строки в Excel пропускается), 34 мероприятия, бонусы = сумма категорий.

## Полезные команды

| Команда | Значение |
|---------|----------|
| `docker compose ps` | Статус контейнеров |
| `docker compose logs api` | Логи бэкенда |
| `docker compose restart api` | Перезапуск API |
| `docker compose exec api python list_users.py` | Список аккаунтов |
| `docker compose exec api python import_excel.py --force` | Импорт из Excel (2-й семестр) |
| `docker compose exec api python seed.py --force --wait 60` | Полный пересид демо-данных |
| `docker compose down -v` | Остановить и **удалить volume БД** (полный сброс данных) |

## Локальная разработка без Docker (как раньше)

Можно по-прежнему поднимать только БД из `backend/project_vuz/Docker-compose.yml`, API через venv и сайт через:

```powershell
python -m http.server 5500 --bind 127.0.0.1
```

В этом режиме `app.js` на порту **5500** обращается к API на **http://127.0.0.1:8000**.

Подробнее про venv и seed без Docker: [backend/project_vuz/README.md](backend/project_vuz/README.md).

## Деплой на VPS

См. [DEPLOY.md](DEPLOY.md).

## Файлы

- `docker-compose.yml` — описание сервисов db, api, web
- `backend/project_vuz/Dockerfile` — образ API
- `docker/Dockerfile.web` + `docker/nginx.conf` — образ фронта с прокси
- `backend/project_vuz/seed.py` — демо-данные
- `backend/project_vuz/list_users.py` — список аккаунтов
- `backend/project_vuz/import_excel.py` — импорт из Excel
