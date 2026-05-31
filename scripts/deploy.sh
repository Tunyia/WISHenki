#!/usr/bin/env bash
# Первый деплой и обновление на VPS (запускать из корня репозитория)
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Файл .env не найден. Скопируйте .env.example в .env и задайте пароли."
  echo "  cp .env.example .env && nano .env"
  exit 1
fi

echo "==> Сборка и запуск контейнеров..."
docker compose -f docker-compose.prod.yml --env-file .env up -d --build

echo "==> Ожидание API..."
sleep 5

if docker compose -f docker-compose.prod.yml --env-file .env exec -T api python seed.py --wait 60; then
  echo "==> Демо-данные загружены (или уже были в БД)."
else
  echo "==> seed завершился с ошибкой — проверьте логи: docker compose -f docker-compose.prod.yml logs api"
  exit 1
fi

echo "==> Готово. Сайт доступен на порту из HTTP_PORT (.env, по умолчанию 80)."
