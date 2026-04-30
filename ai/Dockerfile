# syntax=docker/dockerfile:1.7

############################
# Stage 1 — builder
############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps uniquement pour compiler d'éventuels wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Torch CPU-only (l'index par défaut tirerait CUDA = +2 Go)
RUN pip install --prefix=/install --index-url https://download.pytorch.org/whl/cpu \
  torch==2.4.0

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
COPY data/chroma ./data/chroma
COPY data/processed ./data/processed

# Installe le projet et toutes ses deps dans /install
RUN pip install --prefix=/install .

# Pré-télécharge le modèle d'embeddings dans /models pour éviter
# de le retélécharger à chaque démarrage de container.
ENV HF_HOME=/models \
  SENTENCE_TRANSFORMERS_HOME=/models
RUN PYTHONPATH=/install/lib/python3.11/site-packages \
  python -c "from sentence_transformers import SentenceTransformer; \
  SentenceTransformer('intfloat/multilingual-e5-small')"

############################
# Stage 2 — runtime
############################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  HF_HOME=/models \
  SENTENCE_TRANSFORMERS_HOME=/models \
  HF_HUB_OFFLINE=1 \
  TRANSFORMERS_OFFLINE=1 \
  # Valeurs par défaut surchargeables depuis Coolify
  HOST=0.0.0.0 \
  PORT=8001 \
  OLLAMA_HOST=https://ollama.com \
  CHROMA_DIR=/data/chroma \
  PROCESSED_DIR=/data/processed \
  ASSETS_DIR=/assets

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -r -u 1000 -m -d /home/app app

# Récupère les dépendances Python et le modèle pré-téléchargé
COPY --from=builder /install /usr/local
COPY --from=builder /models /models
COPY --from=builder /app/data /data

# Code applicatif
COPY app ./app
COPY scripts ./scripts
COPY pyproject.toml ./

# Volumes persistants gérés par Coolify (à monter sur /data et /assets)
RUN mkdir -p /data/chroma /data/processed /assets \
  && chown -R app:app /app /data /assets /models

USER app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
