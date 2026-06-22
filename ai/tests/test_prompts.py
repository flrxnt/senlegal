from app.llm.generator import extract_cited_articles, validate_citations
from app.llm.prompts import REFUSAL_TEXT, SYSTEM_PROMPT, build_messages
from app.rag.retriever import RetrievedChunk


def _chunk(num="53"):
    return RetrievedChunk(
        chunk_id="x",
        text="Le seuil est de 50 millions FCFA.",
        score=0.9,
        article_number=num,
        article_title="Seuils",
        document="Code de la Famille",
        volume="Volume 1",
        section="CHAPITRE II",
        page=87,
    )


def test_system_prompt_contains_strict_rules():
    assert "EXCLUSIVEMENT" in SYSTEM_PROMPT
    assert REFUSAL_TEXT in SYSTEM_PROMPT
    assert "[Article" in SYSTEM_PROMPT
    assert "Sources" in SYSTEM_PROMPT


def test_build_messages_includes_context_and_question():
    msgs = build_messages("Quel est le seuil ?", [_chunk()])
    assert msgs[0]["role"] == "system"
    last = msgs[-1]
    assert last["role"] == "user"
    assert "<contexte>" in last["content"]
    assert "Article 53" in last["content"]
    assert "Quel est le seuil ?" in last["content"]


def test_build_messages_empty_context():
    msgs = build_messages("Question ?", [])
    assert "aucun extrait" in msgs[-1]["content"].lower()


def test_extract_cited_articles():
    text = "Le seuil est X [Article 53 — Code de la Famille] et Y [Article premier — Recueil]."
    arts = extract_cited_articles(text)
    assert "53" in arts
    assert "premier" in arts


def test_validate_citations_ok():
    text = "Réponse [Article 53 — Code de la Famille]."
    assert validate_citations(text, [_chunk("53")]) is True


def test_validate_citations_hallucination():
    text = "Réponse [Article 999 — Code de la Famille]."
    assert validate_citations(text, [_chunk("53")]) is False


def test_validate_citations_missing():
    text = "Réponse sans citation."
    assert validate_citations(text, [_chunk("53")]) is False


def test_validate_citations_no_chunks():
    assert validate_citations("[Article 53 — X]", []) is False
