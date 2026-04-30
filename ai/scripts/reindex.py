"""CLI: python -m scripts.reindex [--force]"""
from __future__ import annotations

import argparse
import json
import logging

from app.rag.ingestion import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Réindexe les PDFs dans Chroma.")
    parser.add_argument("--force", action="store_true", help="Reset la collection avant ingestion.")
    args = parser.parse_args()
    result = run_ingestion(force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
