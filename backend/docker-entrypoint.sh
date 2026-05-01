#!/usr/bin/env bash
set -euo pipefail

MIGRATIONS_DIR="prisma/migrations"

if [ -d "$MIGRATIONS_DIR" ] && ls "$MIGRATIONS_DIR"/*/migration.sql >/dev/null 2>&1; then
  echo "[entrypoint] applying migrations..."
  bunx prisma migrate deploy
else
  echo "[entrypoint] no migrations found — syncing schema with db push..."
  bunx prisma db push --skip-generate
fi

if [ "${SEED_ON_BOOT:-false}" = "true" ]; then
  echo "[entrypoint] seeding admin..."
  bun run prisma/seed.ts || true
fi

echo "[entrypoint] starting app: $*"
exec "$@"
