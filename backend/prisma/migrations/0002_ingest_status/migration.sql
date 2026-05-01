-- CreateEnum
CREATE TYPE "IngestStatus" AS ENUM ('PENDING', 'PROCESSING', 'READY', 'FAILED');

-- AlterTable
ALTER TABLE "Document"
ADD COLUMN "ingestStatus" "IngestStatus" NOT NULL DEFAULT 'READY',
ADD COLUMN "ingestStartedAt" TIMESTAMP(3),
ADD COLUMN "ingestError" TEXT;

-- Backfill : les sources RAG existantes déjà indexées sont READY, sinon PENDING
UPDATE "Document"
SET
  "ingestStatus" = 'READY'
WHERE
  "kind" = 'RAG_SOURCE'
  AND "ingestedAt" IS NOT NULL;

UPDATE "Document"
SET
  "ingestStatus" = 'PENDING'
WHERE
  "kind" = 'RAG_SOURCE'
  AND "ingestedAt" IS NULL;

-- CreateIndex
CREATE INDEX "Document_kind_ingestStatus_idx" ON "Document" ("kind", "ingestStatus");