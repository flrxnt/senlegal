# SenLegal AI

Service IA RAG (Retrieval-Augmented Generation) pour répondre aux questions sur le **droit sénégalais** (Code de la Famille et textes connexes), en s'appuyant strictement sur les textes juridiques officiels indexés.

Le service expose une API HTTP (FastAPI) consommée par `backend/`. Il combine :
- **Embeddings** multilingues (`intfloat/multilingual-e5-small`)
- **Base vectorielle** ChromaDB persistante locale
- **LLM** `HuggingFaceTB/SmolLM2-360M-Instruct` (CPU, transformers)
- **Prompt anti-hallucination** strict + **garde-fou de citations** (toute citation à un article inexistant invalide la réponse)

## Installation

```bash
cd ai
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Indexation (à lancer une fois, puis à chaque mise à jour des PDFs)

```bash
python -m scripts.reindex --force
```

Le script lit les PDFs de `assets/`, découpe **par article** (`Article 1`, `Article premier`, `Article 7-1`, …), génère les embeddings et les stocke dans `data/chroma/`.

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Documentation interactive : http://localhost:8001/docs

## Endpoints

### `GET /health`
État du service, nombre de chunks indexés, statut du LLM.

### `POST /search` — recherche RAG seule
```bash
curl -X POST http://localhost:8001/search \
  -H 'content-type: application/json' \
  -d '{"query":"seuil de passation des marchés","top_k":5}'
```

### `POST /chat` — réponse complète avec citations
```bash
curl -X POST http://localhost:8001/chat \
  -H 'content-type: application/json' \
  -d '{"question":"Quel est le seuil pour un appel d offres ouvert ?"}'
```
Réponse :
```json
{
  "answer": "Le seuil ... [Article 53 — ...].\n\nSources :\n- Article 53 — ..., p. 87",
  "citations": [{"article_number":"53","document":"...","page":87,...}],
  "used_context": true
}
```

### `POST /chat/stream` — streaming SSE
Émet d'abord un event `citations` (JSON), puis des events `token` puis `done`.

### `POST /ingest` — ré-indexation (admin)
Header requis : `X-Admin-Token: <token>`. Lance une ingestion en arrière-plan. Variante synchrone : `POST /ingest/sync`.

## Garanties anti-hallucination

1. **Refus déterministe** sans appel au LLM si aucun chunk ne dépasse `MIN_SCORE`.
2. **System prompt strict** : interdit l'usage de connaissances externes, impose la citation `[Article X — document]` après chaque affirmation, impose la phrase de refus exacte si l'info est absente.
3. **Few-shot** intégrant un cas "info présente → citation" et "hors-sujet → refus".
4. **Post-validation** : tout numéro d'article cité absent du contexte invalide la réponse → 1 retry, sinon refus standard.
5. **Température basse** (0.1, `do_sample=False`) pour minimiser la dérive.

## Tests

```bash
pytest
```

## Configuration (`.env`)

| Variable | Défaut | Description |
|---|---|---|
| `MODEL_NAME` | `HuggingFaceTB/SmolLM2-360M-Instruct` | LLM utilisé (swappable) |
| `EMBED_MODEL` | `intfloat/multilingual-e5-small` | Modèle d'embeddings |
| `ASSETS_DIR` | `../assets` | Dossier des PDFs sources |
| `CHROMA_DIR` | `./data/chroma` | Persistance vectorielle |
| `TOP_K` | `5` | Nombre de chunks récupérés |
| `MIN_SCORE` | `0.35` | Score cosinus minimal pour accepter un chunk |
| `MAX_NEW_TOKENS` | `512` | Limite de génération |
| `TEMPERATURE` | `0.1` | Température (0 = déterministe) |
| `ADMIN_TOKEN` | `change-me` | Protège `/ingest` |

## Structure

```
ai/
├── app/
│   ├── api/      # routes FastAPI
│   ├── rag/      # PDF, chunking, embeddings, vectorstore
│   ├── llm/      # modèle, prompts, génération
│   ├── config.py
│   ├── schemas.py
│   └── main.py
├── scripts/reindex.py
├── tests/
├── data/         # chroma + cache (gitignored)
└── Dockerfile
```

## Docker

```bash
docker build -t senlegal-ai ai/
docker run -p 8001:8001 -v $(pwd)/assets:/assets -v $(pwd)/ai/data:/app/data \
  -e ASSETS_DIR=/assets senlegal-ai
```
