# SenLégal — Backend (NestJS + Prisma + Bun)

Backend de la plateforme **SenLégal** : authentification, conversations IA juridiques,
proxy SSE vers le service FastAPI `/ai`, abonnements PayDunya, documents MinIO,
console admin et système de backup.

## Stack

- **Bun** (install + runtime) — `oven/bun:1-alpine`
- **NestJS 11** (HTTP, DI, validation, schedule, throttler, swagger)
- **Prisma 7** + driver `@prisma/adapter-pg` → **PostgreSQL 16**
- **MinIO / S3** via `@aws-sdk/client-s3` (path-style)
- **Nodemailer** (Mailpit en dev)
- **PayDunya** (sandbox/live, IPN signé SHA-512)
- Cron quotidien pour faire expirer automatiquement les abonnements
- Backup full (DB + objets MinIO) zip streamé vers le bucket

## Prérequis

- Bun ≥ 1.1, Node 20+ (pour `nest build`), Docker / Docker Compose pour la stack complète
- PostgreSQL 16 et MinIO accessibles

## Démarrage local

```bash
cd backend
cp .env.example .env
bun install
bunx prisma migrate dev
bun run seed         # crée l'admin (ADMIN_EMAIL/ADMIN_PASSWORD)
bun run dev          # http://localhost:3001/api ; Swagger : /api/docs
```

## Démarrage avec Docker Compose (depuis la racine du repo)

```bash
docker compose up -d --build
# - postgres   : localhost:5433
# - minio      : http://localhost:9000  (console http://localhost:9001)
# - mailpit    : http://localhost:8025
# - ai         : http://localhost:8001/health
# - backend    : http://localhost:3001/api/health  (Swagger : /api/docs)
```

L'utilisateur admin est créé au boot via `SEED_ON_BOOT=true` (variables `ADMIN_EMAIL`,
`ADMIN_PASSWORD`).

## Endpoints principaux

Tous les endpoints sont préfixés par `/api`.

### Public

- `POST /auth/register` `POST /auth/login`
- `POST /auth/forgot-password` `POST /auth/reset-password`
- `POST /payments/webhook/paydunya` (IPN, hash SHA-512)
- `GET /health`

### Utilisateur (Bearer JWT)

- `GET/PATCH /me` — profil
- `POST /me/password` — changement de mot de passe
- `POST /me/avatar` (multipart `file`) — avatar utilisateur
- `GET/POST /me/documents` `DELETE /me/documents/:id` — coffre-fort
- `GET /documents/:id/url` — URL signée (5 min)
- `GET/POST/PATCH/DELETE /chat/conversations[/:id]`
- `POST /chat/conversations/:id/messages` — envoi non-streamé
- `POST /chat/conversations/:id/stream` — **SSE** proxifié (`event: citations`, `event: token`, `event: done`)
- `POST /payments/checkout` `{ plan: "PRO" }` → `{ checkoutUrl }`
- `POST /payments/reconcile/:invoiceId` — réconciliation manuelle au retour
- `GET /payments/me/invoices`
- `GET /me/subscriptions` `POST /me/subscriptions/cancel`

### Admin (`role=ADMIN`)

- `GET /admin/stats`
- `GET/PATCH/DELETE /admin/users[/:id]`
- `GET /admin/conversations` `GET /admin/invoices`
- `GET /admin/errors` `GET /admin/events`
- `GET/POST/DELETE /admin/rag/sources` — ingestion documents RAG (forwarded to AI `/ingest`)
- Backups :
  - `GET /admin/backups` (liste)
  - `POST /admin/backups/database` (JSON dump)
  - `POST /admin/backups/full` (zip streamé : DB + objets MinIO)
  - `GET /admin/backups/:key/url` (URL signée 10 min)
  - `DELETE /admin/backups/:key`
  - `POST /admin/backups/restore` (multipart `file`, `.json` ou `.zip`)

## Sécurité — points clés

- **JWT HS256** (`JWT_SECRET` ≥ 32 caractères en prod), validation Passport + reflector-based guards.
- **bcrypt** rounds 12 (configurable).
- **Helmet** + **ValidationPipe** strict (whitelist + forbidNonWhitelisted).
- **Throttler** global 120 req/min/IP, plus throttle local (10/min sur register, 20/min sur login,
  30/min sur chat).
- **PayDunya IPN** : vérification du hash `sha512(masterKey).hex === payload.hash` ;
  finalize sous **`pg_advisory_xact_lock`** + transaction → idempotent face aux re-livraisons.
- **Quotas plan** centralisés (`PlanLimitsService`) : msg/jour FREE = 5, stockage FREE = 50 MB.
- **All exceptions filter** : journalise tout `>= 500` dans `ErrorLog` (visible via `/admin/errors`).
- L'utilisateur final ne contacte **jamais** directement le service AI : la clé `AI_API_KEY` reste
  côté backend.

## Cron

`SubscriptionsScheduler` tourne tous les jours à 03:00 (Africa/Dakar par défaut serveur).
Il marque `EXPIRED` toute souscription `ACTIVE` dont `currentPeriodEnd <= now`, puis si
l'utilisateur n'a plus aucun abonnement actif, repasse `User.plan = FREE` et envoie un email.
Désactivable via `SUBSCRIPTIONS_SCHEDULER_ENABLED=false`.

Run manuel : `bun run subscriptions:expire`.

## Migrations

```bash
bunx prisma migrate dev --name init    # local
bunx prisma migrate deploy             # production (entrypoint)
```

## Tests / lint

```bash
bun run lint    # tsc --noEmit
bun run build   # nest build
```
