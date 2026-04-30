from unittest.mock import MagicMock, patch

import numpy as np

from app.rag import retriever


def _make_collection(results_per_query):
    """results_per_query: list of dicts shaped like Chroma's `query` return."""
    fake_col = MagicMock()
    fake_col.count.return_value = 10
    fake_col.query.side_effect = results_per_query
    return fake_col


def test_retrieve_multi_merges_and_keeps_best_score(tmp_path):
    fake_col = _make_collection([
        {
            "ids": [["a", "b"]],
            "documents": [["A", "B"]],
            "metadatas": [[
                {"article_number": "1", "document": "Doc", "page_start": 1, "article_title": ""},
                {"article_number": "2", "document": "Doc", "page_start": 2, "article_title": ""},
            ]],
            "distances": [[0.4, 0.2]],  # scores 0.6 et 0.8
        },
        {
            "ids": [["b", "c"]],
            "documents": [["B", "C"]],
            "metadatas": [[
                {"article_number": "2", "document": "Doc", "page_start": 2, "article_title": ""},
                {"article_number": "3", "document": "Doc", "page_start": 3, "article_title": ""},
            ]],
            "distances": [[0.05, 0.5]],  # scores 0.95 et 0.5
        },
    ])

    with patch.object(retriever, "get_collection", return_value=fake_col), \
         patch.object(retriever, "embed_query", return_value=np.zeros(8)):
        out = retriever.retrieve_multi(
            queries=["q1", "q2"],
            chroma_dir=tmp_path,
            collection_name="c",
            embed_model="m",
            top_k=3,
            min_score=0.0,
        )

    assert [c.chunk_id for c in out] == ["b", "a", "c"]
    # le score de b doit être celui de la 2e requête (0.95)
    assert out[0].score > 0.9


def test_retrieve_multi_dedupes_queries(tmp_path):
    fake_col = _make_collection([
        {
            "ids": [["a"]],
            "documents": [["A"]],
            "metadatas": [[{"article_number": "1", "document": "Doc", "page_start": 1, "article_title": ""}]],
            "distances": [[0.1]],
        },
    ])

    with patch.object(retriever, "get_collection", return_value=fake_col), \
         patch.object(retriever, "embed_query", return_value=np.zeros(8)):
        out = retriever.retrieve_multi(
            queries=["même question", "Même Question  ", ""],
            chroma_dir=tmp_path,
            collection_name="c",
            embed_model="m",
            top_k=3,
            min_score=0.0,
        )

    assert len(out) == 1
    assert fake_col.query.call_count == 1


def test_retrieve_multi_empty_queries(tmp_path):
    with patch.object(retriever, "get_collection") as gc:
        out = retriever.retrieve_multi(
            queries=["", None, "   "],  # type: ignore[list-item]
            chroma_dir=tmp_path,
            collection_name="c",
            embed_model="m",
            top_k=3,
        )
    assert out == []
    gc.assert_not_called()
