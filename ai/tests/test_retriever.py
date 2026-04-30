from unittest.mock import MagicMock, patch

import numpy as np

from app.rag import retriever


def test_retrieve_filters_by_score(tmp_path):
    fake_col = MagicMock()
    fake_col.count.return_value = 2
    fake_col.query.return_value = {
        "ids": [["a", "b"]],
        "documents": [["chunk A", "chunk B"]],
        "metadatas": [[
            {"article_number": "1", "document": "Doc", "page_start": 1, "article_title": ""},
            {"article_number": "2", "document": "Doc", "page_start": 2, "article_title": ""},
        ]],
        # distance cosinus : 0.1 -> score 0.9 (gardé), 0.8 -> score 0.2 (filtré)
        "distances": [[0.1, 0.8]],
    }

    with patch.object(retriever, "get_collection", return_value=fake_col), \
         patch.object(retriever, "embed_query", return_value=np.zeros(8)):
        out = retriever.retrieve(
            query="test",
            chroma_dir=tmp_path,
            collection_name="c",
            embed_model="m",
            top_k=5,
            min_score=0.5,
        )

    assert len(out) == 1
    assert out[0].chunk_id == "a"
    assert out[0].score > 0.5


def test_retrieve_empty_collection(tmp_path):
    fake_col = MagicMock()
    fake_col.count.return_value = 0
    with patch.object(retriever, "get_collection", return_value=fake_col):
        out = retriever.retrieve(
            query="x",
            chroma_dir=tmp_path,
            collection_name="c",
            embed_model="m",
            top_k=5,
        )
    assert out == []
