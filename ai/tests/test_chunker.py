from app.rag.chunker import chunk_documents
from app.rag.pdf_loader import PageText


SAMPLE = """LIVRE I — DISPOSITIONS GENERALES

TITRE I — CHAMP D'APPLICATION

Article premier. Objet
Le présent Code fixe les règles applicables aux marchés publics
passés par les autorités contractantes au Sénégal.

Article 2. Définitions
Au sens du présent Code, on entend par marché public tout contrat
écrit conclu à titre onéreux.

CHAPITRE II — Procédures

Article 53. Seuils
Le seuil de l'appel d'offres ouvert est fixé à 50 millions de FCFA
pour les fournitures et services courants.
"""


def _pages():
    return [PageText(document="Code des marchés", volume="Volume 1", page=1, text=SAMPLE)]


def test_chunker_detects_articles():
    chunks = chunk_documents(_pages(), max_chunk_chars=1500)
    arts = [c.article_number for c in chunks]
    assert "premier" in arts
    assert "2" in arts
    assert "53" in arts


def test_chunker_keeps_section_context():
    chunks = chunk_documents(_pages())
    by_art = {c.article_number: c for c in chunks}
    assert by_art["premier"].section is not None
    assert "TITRE" in by_art["premier"].section.upper() or "LIVRE" in by_art["premier"].section.upper()
    # L'article 53 devrait remonter le CHAPITRE II
    assert by_art["53"].section is not None
    assert "CHAPITRE" in by_art["53"].section.upper()


def test_chunker_metadata():
    chunks = chunk_documents(_pages())
    for c in chunks:
        assert c.document == "Code des marchés"
        assert c.volume == "Volume 1"
        assert c.page_start == 1
        assert c.chunk_id  # non vide
        assert c.text.lower().startswith("article")


DECRET_SAMPLE = """TITRE V — RÉGIMES PRÉFÉRENTIELS

Section V. - Régimes préférentiels

Art. 50. - Pour les marchés passés sur appel d'offres international,
une préférence est accordée aux candidats de droit sénégalais ou de
pays membres de l'UEMOA.

Art. 51. - Pour bénéficier de la préférence, les candidats doivent
joindre les pièces justificatives à leur offre.

Art. 7-1 : Cas particuliers
Le présent article s'applique aux marchés mixtes.
"""


def _decret_pages():
    return [
        PageText(
            document="Recueil — décret",
            volume="Volume 1",
            page=15,
            text=DECRET_SAMPLE,
        )
    ]


def test_chunker_detects_abbreviated_articles():
    """Les décrets utilisent la forme abrégée 'Art. 50.' qui doit être reconnue."""
    chunks = chunk_documents(_decret_pages())
    arts = sorted(c.article_number for c in chunks)
    assert arts == ["50", "51", "7-1"]


def test_chunker_does_not_split_on_inline_art_mention():
    """Une mention 'art. X' au milieu d'une phrase ne doit PAS créer de chunk."""
    pages = [
        PageText(
            document="Doc",
            volume=None,
            page=1,
            text=(
                "Article 10. Dispositions\n"
                "Le présent article renvoie aux dispositions de l'art. 5 du décret.\n"
                "Il complète également l'art. 12 ci-après.\n"
            ),
        )
    ]
    chunks = chunk_documents(pages)
    arts = [c.article_number for c in chunks]
    assert arts == ["10"]
