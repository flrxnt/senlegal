from app.llm import query_rewriter


def test_basic_cleanup_trims_spacing_and_punctuation():
    cleaned = query_rewriter._basic_cleanup("  c est   quoi  une   DRP ?  ")
    assert cleaned == "C'est quoi une DRP?"


def test_rewrite_query_uses_fallback_when_llm_fails(monkeypatch):
    monkeypatch.setattr(query_rewriter, "get_client", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert query_rewriter.rewrite_query("  c est quoi   une prestation intellectuelle ? ") == (
        "C'est quoi une prestation intellectuelle?"
    )


def test_rewrite_query_rejects_unsafe_rewrite(monkeypatch):
    class FakeClient:
        def chat(self, **kwargs):
            return {"message": {"content": "Explique-moi la procédure complète d'appel d'offres."}}

    monkeypatch.setattr(query_rewriter, "get_client", lambda: FakeClient())
    assert query_rewriter.rewrite_query("c est quoi une DRP ?") == "C'est quoi une DRP?"


def test_rewrite_query_accepts_safe_rewrite(monkeypatch):
    class FakeClient:
        def chat(self, **kwargs):
            return {"message": {"content": "C'est quoi une DRP ?"}}

    monkeypatch.setattr(query_rewriter, "get_client", lambda: FakeClient())
    assert query_rewriter.rewrite_query("c est quoi une DRP ?") == "C'est quoi une DRP?"