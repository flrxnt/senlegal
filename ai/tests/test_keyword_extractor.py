from app.llm import keyword_extractor


def test_parse_keywords_extracts_clean_list():
    raw = '{"keywords": ["candidat évincé", "  recours  ", "ARCOP", "", "candidat évincé"]}'
    assert keyword_extractor._parse_keywords(raw) == [
        "candidat évincé",
        "recours",
        "ARCOP",
    ]


def test_parse_keywords_handles_garbage():
    assert keyword_extractor._parse_keywords("pas de json ici") == []
    assert keyword_extractor._parse_keywords("") == []
    assert keyword_extractor._parse_keywords('{"keywords": "string au lieu de liste"}') == []


def test_parse_keywords_extracts_object_inside_text():
    raw = 'Voici: {"keywords": ["AOO", "AOR"]} fin'
    assert keyword_extractor._parse_keywords(raw) == ["AOO", "AOR"]


def test_extract_keywords_returns_empty_when_disabled(monkeypatch):
    from app import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("KEYWORD_EXTRACTION_ENABLED", "false")
    try:
        assert keyword_extractor.extract_keywords("question quelconque") == []
    finally:
        monkeypatch.delenv("KEYWORD_EXTRACTION_ENABLED", raising=False)
        config.get_settings.cache_clear()


def test_extract_keywords_returns_empty_on_llm_error(monkeypatch):
    monkeypatch.setattr(
        keyword_extractor,
        "get_client",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert keyword_extractor.extract_keywords("question quelconque") == []


def test_extract_keywords_parses_llm_response(monkeypatch):
    class FakeClient:
        def chat(self, **kwargs):
            return {
                "message": {
                    "content": '{"keywords": ["candidat évincé", "recours", "CRD"]}'
                }
            }

    monkeypatch.setattr(keyword_extractor, "get_client", lambda: FakeClient())
    out = keyword_extractor.extract_keywords("Je n'ai pas été sélectionné, que faire ?")
    assert out == ["candidat évincé", "recours", "CRD"]


def test_build_enriched_query_appends_keywords():
    enriched = keyword_extractor.build_enriched_query(
        "question?", ["candidat évincé", "recours"]
    )
    assert enriched == "question? | mots-clés: candidat évincé, recours"


def test_build_enriched_query_returns_question_when_no_keywords():
    assert keyword_extractor.build_enriched_query("question?", []) == "question?"
