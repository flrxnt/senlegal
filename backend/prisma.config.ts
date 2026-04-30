import 'dotenv/config';
import path from 'node:path';
import { defineConfig } from 'prisma/config';

export default defineConfig({
  schema: path.join('prisma', 'schema.prisma'),
  migrations: {
    path: path.join('prisma', 'migrations'),
    seed: 'bun run prisma/seed.ts',
  },
  datasource: {
    // Empty fallback only used at build-time for `prisma generate` (no DB needed).
    // At runtime, DATABASE_URL is always set by the environment / docker-compose.
    url: process.env.DATABASE_URL ?? 'postgresql://user:pass@localhost:5432/placeholder',
  },
});
