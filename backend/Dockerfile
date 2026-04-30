# --- Stage 1: install + build ---------------------------------------------
FROM oven/bun:1-alpine AS builder

WORKDIR /app

# OpenSSL is required by Prisma engines on alpine
RUN apk add --no-cache openssl libc6-compat

COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install

COPY tsconfig.json tsconfig.build.json nest-cli.json prisma.config.ts ./
COPY prisma ./prisma
COPY src ./src
COPY scripts ./scripts

RUN bunx prisma generate
RUN bun run build

# --- Stage 2: runtime -----------------------------------------------------
FROM oven/bun:1-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production
RUN apk add --no-cache openssl libc6-compat tini bash

COPY package.json bun.lock* ./
RUN bun install --production --frozen-lockfile || bun install --production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/prisma.config.ts ./prisma.config.ts
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma ./node_modules/@prisma
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 3001
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["bun", "run", "dist/main.js"]
