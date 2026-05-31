# Деплой WISHenki на VPS (демо)

Инструкция для демонстрационного сайта на Linux VPS. Стек: Docker Compose (PostgreSQL + FastAPI + nginx).

## Какие характеристики VPS нужны

Для **до 30 человек одновременно** (учебный проект, лёгкий трафик):

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| CPU | 1 vCPU | **2 vCPU** |
| RAM | 1 GB | **2 GB** |
| Диск | 10 GB SSD | **20 GB SSD** |
| ОС | Ubuntu 22.04 / 24.04 LTS | то же |

**1 GB RAM** может хватить, но Docker + PostgreSQL + 2 worker'а uvicorn будут впритык. Для спокойной демонстрации лучше **2 GB**.

Провайдеры: Timeweb, Selectel, REG.RU, Hetzner, DigitalOcean и т.п. — любой VPS с Ubuntu и root/sudo.

---

## 1. Подготовка сервера

Подключитесь по SSH:

```bash
ssh root@ВАШ_IP
```

Установите Docker (официальный скрипт):

```bash
apt-get update
apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
```

Проверка:

```bash
docker compose version
```

Откройте порты (если включён ufw):

```bash
ufw allow OpenSSH
ufw allow 80/tcp
# ufw allow 443/tcp   # когда подключите HTTPS
ufw enable
```

---

## 2. Клонирование проекта

```bash
cd /opt
git clone https://github.com/ВАШ_АККАУНТ/WISHenki.git
cd WISHenki
```

Если репозиторий приватный — настройте SSH-ключ на сервере или используйте deploy token.

---

## 3. Файл `.env` (секреты)

```bash
cp .env.example .env
nano .env
```

Задайте **уникальные** значения:

```env
POSTGRES_USER=wishenki
POSTGRES_PASSWORD=длинный_случайный_пароль
POSTGRES_DB=vish_rating
SECRET_KEY=другой_длинный_случайный_ключ
HTTP_PORT=80
```

Сгенерировать пароли на сервере:

```bash
openssl rand -hex 32
```

Файл `.env` **не коммитьте** в git.

---

## 4. Первый запуск

```bash
chmod +x scripts/deploy.sh scripts/backup-db.sh
./scripts/deploy.sh
```

Скрипт:

1. собирает и поднимает контейнеры (`docker-compose.prod.yml`);
2. загружает демо-данные (`seed.py` **без** `--force`).

Сайт: **http://ВАШ_IP** (или `:8080`, если в `.env` указали `HTTP_PORT=8080`).

Проверка с сервера:

```bash
curl -I http://127.0.0.1/
docker compose -f docker-compose.prod.yml exec api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"
```

---

## 5. Обновление после изменений в коде

На **локальной машине** — commit + push. На **сервере**:

```bash
cd /opt/WISHenki
git pull
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Или снова:

```bash
./scripts/deploy.sh
```

> **Не правьте код напрямую на сервере.** Разработка локально → git → pull на VPS.

---

## 6. Полезные команды

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f

# Статус
docker compose -f docker-compose.prod.yml ps

# Перезапуск
docker compose -f docker-compose.prod.yml --env-file .env restart

# Бэкап БД
./scripts/backup-db.sh

# Список зарегистрированных аккаунтов (email + студент, без паролей)
docker compose -f docker-compose.prod.yml --env-file .env exec api python list_users.py

# Все студенты рейтинга, включая без аккаунта
docker compose -f docker-compose.prod.yml --env-file .env exec api python list_users.py --all-students

# Импорт из Excel (2-й семестр)
docker compose -f docker-compose.prod.yml --env-file .env exec api python import_excel.py --dry-run
docker compose -f docker-compose.prod.yml --env-file .env exec api python import_excel.py --force

# Меню администратора (интерактивное CRUD-меню, флаг -it)
docker compose -f docker-compose.prod.yml --env-file .env exec -it api python admin_menu.py

# Полный сброс демо-данных (ОСТОРОЖНО — удалит все данные!)
docker compose -f docker-compose.prod.yml exec api python seed.py --force --wait 60
```

Подробная инструкция по `admin_menu.py` (разделы меню, сброс пароля, запись на мероприятия): [DOCKER.md](DOCKER.md#меню-администратора-admin_menupy).

> **Аккаунты vs рейтинг:** `seed.py` создаёт студентов для таблицы лидеров, но не логины.  
> В `list_users.py` попадают только те, кто **зарегистрировался** на сайте.  
> После обновления скриптов на сервере: `git pull` и `docker compose -f docker-compose.prod.yml --env-file .env up -d --build api`.

---

## 7. HTTPS (опционально, если есть домен)

Для демо по IP достаточно HTTP. Если есть домен (например `wishenki.example.com`), проще всего поставить **Caddy** на хост перед Docker:

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy
```

В `/etc/caddy/Caddyfile`:

```
wishenki.example.com {
    reverse_proxy localhost:80
}
```

В `.env` можно сменить `HTTP_PORT=8080`, чтобы Caddy слушал 443/80, а Docker — только localhost:8080. Тогда в `docker-compose.prod.yml` замените проброс порта на `"127.0.0.1:${HTTP_PORT:-8080}:80"`.

---

## Отличия prod от локальной разработки

| | Локально (`docker-compose.yml`) | VPS (`docker-compose.prod.yml`) |
|--|-----------------------------------|----------------------------------|
| Порты | 8080 (web), 8000 (api) | только **80** (web), api/db внутри сети |
| Пароли | `postgres` / dev | из `.env` |
| JWT | dev-ключ по умолчанию | **SECRET_KEY** из `.env` |
| uvicorn | 1 worker | 2 workers |
| nginx | dev | prod + no-cache для html/css/js |

Локальная разработка по-прежнему:

```bash
docker compose up --build
# сайт: http://127.0.0.1:8080
```
