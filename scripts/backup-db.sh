#!/usr/bin/env bash
# Резервная копия PostgreSQL (запускать из корня репозитория)
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Нужен файл .env"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

mkdir -p backups
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="backups/wishenki_${STAMP}.sql.gz"

docker compose -f docker-compose.prod.yml --env-file .env exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"

echo "Бэкап сохранён: $FILE"
