#!/usr/bin/env python3
"""
Génération de datasets d'entraînement et de test à partir des textes
juridiques sénégalais (Code de la Famille et autres textes indexés).

Utilise le pipeline de parsing/chunking du projet SenLegal,
puis génère des paires Q/A via Ollama Cloud (Gemma 4 31B).
"""

import json
import os
import random
import sys
import time
from pathlib import Path

import ollama

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ai"))
from app.rag.pdf_loader import load_pdf
from app.rag.chunker import chunk_documents

PDF_VOL1 = Path("/Users/administrator/Downloads/RECUEIL-DES-TEXTES-JURIDIQUES-DE-LA-COMMANDE-PUBLIQUE-AU-SENEGAL-VOL-1-EDITION-2023-2.pdf")
PDF_VOL2 = Path("/Users/administrator/Downloads/RECUEIL-DES-TEXTES-JURIDIQUES-DE-LA-COMMANDE-PUBLIQUE-AU-SENEGAL-VOL-2-EDITION-2023.pdf")

OLLAMA_HOST = "https://ollama.com"
OLLAMA_API_KEY = "9c9af35202044cda8501aa7c4e4ea88b.Y562r4ZKHoNU02-LGY4r5jxM"
MODEL = "gemma4:31b-cloud"

OUT_DIR = Path(__file__).parent / "datasets"
TRAIN_SPLIT = 0.80
SEED = 42

QA_GENERATION_PROMPT = """Tu es un expert du droit sénégalais (Code de la Famille et textes connexes). À partir de l'extrait juridique ci-dessous, génère exactement {n} paires question-réponse au format JSON.

Règles :
- Les questions doivent être variées : définitions, conditions, procédures, obligations, distinctions, rôles.
- Les réponses doivent être précises, complètes et fidèles au texte source. Cite l'article quand c'est pertinent.
- Les questions doivent pouvoir être posées par un praticien du droit, un étudiant ou un citoyen.
- Pas de questions triviales (oui/non simple). Préfère des questions ouvertes ou à développement court.
- Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ou après.

Format attendu :
[
  {{"question": "...", "answer": "...", "article": "...", "source": "..."}},
  ...
]

--- EXTRAIT ---
Source : {source}
Article : {article}
Section : {section}

{text}
--- FIN EXTRAIT ---

Génère {n} paires question-réponse JSON :"""


def init_ollama():
    client = ollama.Client(
        host=OLLAMA_HOST,
        headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
    )
    return client


def parse_pdfs():
    """Parse les 2 volumes PDF et retourne les chunks."""
    print("=== Parsing des PDFs ===")
    pages = []
    for pdf_path in [PDF_VOL1, PDF_VOL2]:
        print(f"  Lecture de {pdf_path.name}...")
        pdf_pages = load_pdf(pdf_path)
        print(f"    → {len(pdf_pages)} pages extraites")
        pages.extend(pdf_pages)

    print(f"\n  Total pages : {len(pages)}")
    print("  Chunking par article...")
    chunks = chunk_documents(pages, max_chunk_chars=2000)
    print(f"  → {len(chunks)} chunks générés")

    chunks = [c for c in chunks if len(c.text.strip()) > 100]
    print(f"  → {len(chunks)} chunks après filtrage (>100 chars)")
    return chunks


def generate_qa_pairs(client, chunk, n_questions=3):
    """Génère n paires Q/A à partir d'un chunk via le LLM."""
    if len(chunk.text.strip()) < 150:
        n_questions = 1
    elif len(chunk.text.strip()) < 400:
        n_questions = 2

    prompt = QA_GENERATION_PROMPT.format(
        n=n_questions,
        source=chunk.document,
        article=f"Article {chunk.article_number}" if chunk.article_number else "N/A",
        section=chunk.section or "N/A",
        text=chunk.text[:3000],
    )

    try:
        response = client.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 2048},
            keep_alive="30m",
        )
        content = response.message.content.strip()

        # Extract JSON from response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            return []

        json_str = content[start:end]
        pairs = json.loads(json_str)

        for pair in pairs:
            pair["source_document"] = chunk.document
            pair["source_volume"] = chunk.volume
            pair["source_section"] = chunk.section
            pair["source_article"] = chunk.article_number
            pair["source_page"] = chunk.page_start
            pair["chunk_text"] = chunk.text[:500]

        return pairs

    except json.JSONDecodeError:
        return []
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []


def main():
    OUT_DIR.mkdir(exist_ok=True)
    random.seed(SEED)

    # Step 1: Parse PDFs
    chunks = parse_pdfs()

    # Step 2: Generate Q/A pairs
    print(f"\n=== Génération des paires Q/A via {MODEL} ===")
    print(f"  Chunks à traiter : {len(chunks)}")
    print(f"  Questions par chunk : 2-3")
    print(f"  Estimation : {len(chunks) * 2.5:.0f} paires Q/A")
    print()

    client = init_ollama()
    all_pairs = []
    errors = 0

    for i, chunk in enumerate(chunks):
        q_num = i + 1
        short = chunk.text[:60].replace("\n", " ")
        n_q = 3 if len(chunk.text) >= 400 else (2 if len(chunk.text) >= 150 else 1)

        print(f"  [{q_num:3d}/{len(chunks)}] Art. {chunk.article_number:<12s} | {chunk.document[:45]:<45s} | {n_q}Q")

        pairs = generate_qa_pairs(client, chunk, n_questions=n_q)
        if pairs:
            all_pairs.extend(pairs)
            print(f"           → {len(pairs)} paires générées")
        else:
            errors += 1
            print(f"           → ECHEC")

        # Save intermediate results every 50 chunks
        if q_num % 50 == 0:
            _save_intermediate(all_pairs, q_num)

        time.sleep(0.5)

    print(f"\n  Total paires générées : {len(all_pairs)}")
    print(f"  Erreurs : {errors}/{len(chunks)}")

    # Step 3: Deduplicate
    seen = set()
    unique_pairs = []
    for p in all_pairs:
        key = p["question"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique_pairs.append(p)
    print(f"  Paires uniques : {len(unique_pairs)} (dédupliquées de {len(all_pairs)})")

    # Step 4: Split into train / test
    random.shuffle(unique_pairs)
    split_idx = int(len(unique_pairs) * TRAIN_SPLIT)
    train_set = unique_pairs[:split_idx]
    test_set = unique_pairs[split_idx:]

    print(f"\n=== Répartition ===")
    print(f"  Entraînement : {len(train_set)} paires ({TRAIN_SPLIT*100:.0f}%)")
    print(f"  Test :          {len(test_set)} paires ({(1-TRAIN_SPLIT)*100:.0f}%)")

    # Step 5: Save datasets
    _save_datasets(train_set, test_set, unique_pairs)


def _save_intermediate(pairs, chunk_num):
    path = OUT_DIR / "qa_pairs_intermediate.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"           💾 Sauvegarde intermédiaire ({len(pairs)} paires)")


def _save_datasets(train_set, test_set, all_pairs):
    # JSON format
    for name, data in [("train", train_set), ("test", test_set), ("all", all_pairs)]:
        path = OUT_DIR / f"senlegal_{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 {path} ({len(data)} paires)")

    # JSONL format (for fine-tuning)
    for name, data in [("train", train_set), ("test", test_set)]:
        path = OUT_DIR / f"senlegal_{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                entry = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es SenLégal, un assistant juridique IA spécialisé dans le droit sénégalais (Code de la Famille et textes connexes). Tu réponds de manière précise en citant les articles et sources juridiques pertinents."
                        },
                        {"role": "user", "content": item["question"]},
                        {"role": "assistant", "content": item["answer"]},
                    ],
                    "metadata": {
                        "article": item.get("source_article", ""),
                        "source": item.get("source_document", ""),
                        "section": item.get("source_section", ""),
                    }
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"  💾 {path} (JSONL fine-tuning)")

    # CSV format (for evaluation / spreadsheets)
    import csv
    for name, data in [("train", train_set), ("test", test_set)]:
        path = OUT_DIR / f"senlegal_{name}.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "question", "answer", "article", "source",
                "source_document", "source_volume", "source_section",
                "source_article", "source_page",
            ])
            writer.writeheader()
            for item in data:
                writer.writerow({
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "article": item.get("article", ""),
                    "source": item.get("source", ""),
                    "source_document": item.get("source_document", ""),
                    "source_volume": item.get("source_volume", ""),
                    "source_section": item.get("source_section", ""),
                    "source_article": item.get("source_article", ""),
                    "source_page": item.get("source_page", ""),
                })
        print(f"  💾 {path} (CSV)")

    # Stats summary
    stats = {
        "total_pairs": len(all_pairs),
        "train_pairs": len(train_set),
        "test_pairs": len(test_set),
        "split_ratio": f"{TRAIN_SPLIT*100:.0f}/{(1-TRAIN_SPLIT)*100:.0f}",
        "sources": list(set(p.get("source_document", "") for p in all_pairs)),
        "articles_covered": len(set(p.get("source_article", "") for p in all_pairs)),
        "sections_covered": len(set(p.get("source_section", "") for p in all_pairs if p.get("source_section"))),
    }
    stats_path = OUT_DIR / "dataset_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  📊 {stats_path}")

    print("\n=== Terminé ===")
    print(f"  Dossier : {OUT_DIR}")


if __name__ == "__main__":
    main()
