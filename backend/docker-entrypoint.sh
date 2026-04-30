#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] running prisma migrate deploy..."
bunx prisma migrate deploy || {
  echo "[entrypoint] migrate deploy failed — attempting db push as fallback"
  bunx prisma db push --accept-data-loss=false
}

if [ "${SEED_ON_BOOT:-false}" = "true" ]; then
  echo "[entrypoint] seeding admin..."
  bun run prisma/seed.ts || true
fi

echo "[entrypoint] starting app: $*"
exec "$@"
