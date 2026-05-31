# Запуск проекта в Docker

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

## Демо-данные (студенты, мероприятия)

После первого `up` таблицы создаются автоматически, но **данные** нужно залить один раз:

```powershell
docker compose exec api python seed.py
```

Полный сброс и перезаливка:

```powershell
docker compose down -v
docker compose up --build -d
docker compose exec api python seed.py --force --wait 60
```

## Полезные команды

| Команда | Значение |
|---------|----------|
| `docker compose ps` | Статус контейнеров |
| `docker compose logs api` | Логи бэкенда |
| `docker compose restart api` | Перезапуск API |
| `docker compose exec api python list_users.py` | Список аккаунтов |
| `docker compose down -v` | Остановить и **удалить volume БД** (полный сброс данных) |

> Актуальная версия этого файла — [DOCKER.md](../DOCKER.md) в корне репозитория.

## Локальная разработка без Docker (как раньше)

Можно по-прежнему поднимать только БД из `backend/project_vuz/Docker-compose.yml`, API через venv и сайт через:

```powershell
python -m http.server 5500 --bind 127.0.0.1
```

В этом режиме `app.js` на порту **5500** обращается к API на **http://127.0.0.1:8000**.

## Файлы

- `docker-compose.yml` — описание сервисов db, api, web
- `backend/project_vuz/Dockerfile` — образ API
- `docker/Dockerfile.web` + `docker/nginx.conf` — образ фронта с прокси
