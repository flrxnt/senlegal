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


# ---------------------------------------------------------------------------
# Tests d\u00e9cisions ARCOP / CRD
# ---------------------------------------------------------------------------

DECISION_SAMPLE = """DECISION N\u00b0041/2026/ARCOP/CRD/DEF DU 1er AVRIL 2026
DU COMITE DE REGLEMENT DES DIFFERENDS SUR LE RECOUR DU GROUPEMENT...

LA CHAMBRE DES MARCHES PUBLICS DU COMITE DE REGLEMENT DES DIFFERENDS
STATUANT EN COMMISSION LITIGES,

Vu la loi n\u00b02022-07 du 19 avril 2022 ...
Vu le d\u00e9cret n\u00b02022-2295 du 28 d\u00e9cembre 2022 portant Code des march\u00e9s publics ;

LES FAITS

La SAED a obtenu, dans le cadre du Programme DELTA, un financement de l'AFD,
pour financer les travaux d'am\u00e9nagement des casiers de Dagana A et B.

LES MOYENS DEVELOPPES A L'APPUI DU RECOURS

Le groupement informe qu'un premier appel d'offres r\u00e9f\u00e9renc\u00e9 n\u00b0 2023/04 a \u00e9t\u00e9
pass\u00e9 en 2023.

LES MOTIFS DONNES PAR L'AUTORITE CONTRACTANTE

La SAED rappelle que la proc\u00e9dure initiale n\u00b02023/04 ne couvrait que les
travaux de terrassement.

OBJET DU LITIGE

Il r\u00e9sulte de la saisine que le litige porte sur la r\u00e9gularit\u00e9 de la proc\u00e9dure.

EXAMEN DU LITIGE

Sur l'absence de notification pr\u00e9alable de l'annulation de la proc\u00e9dure initiale :

Consid\u00e9rant qu'il ressort de l'article 65 du Code des March\u00e9s publics ...

PAR CES MOTIFS :

1) Constate que l'annulation de la proc\u00e9dure initiale et la relance du march\u00e9
ont \u00e9t\u00e9 effectu\u00e9es apr\u00e8s obtention des avis de non-objection de l'AFD ;
2) Rejette en cons\u00e9quence le recours comme non fond\u00e9 ;
"""


def _decision_pages():
    return [
        PageText(
            document="D\u00e9cision N\u00b0041/2026/ARCOP/CRD/DEF du 1er avril 2026",
            volume=None,
            page=1,
            text=DECISION_SAMPLE,
            doc_type="decision",
            decision_number="N\u00b0041/2026/ARCOP/CRD/DEF",
            decision_date="1er avril 2026",
        )
    ]


def test_chunker_detects_decision_sections():
    chunks = chunk_documents(_decision_pages())
    keys = [c.article_number for c in chunks]
    # Toutes les sections canoniques doivent \u00eatre rep\u00e9r\u00e9es
    assert "FAITS" in keys
    assert "MOYENS_REQUERANT" in keys
    assert "MOTIFS_AUTORITE" in keys
    assert "OBJET" in keys
    assert "EXAMEN" in keys
    assert "DISPOSITIF" in keys


def test_chunker_decision_metadata():
    chunks = chunk_documents(_decision_pages())
    for c in chunks:
        assert c.doc_type == "decision"
        assert c.decision_number == "N\u00b0041/2026/ARCOP/CRD/DEF"
        assert c.decision_date == "1er avril 2026"
        assert c.section == "N\u00b0041/2026/ARCOP/CRD/DEF"


def test_chunker_decision_dispositif_contains_par_ces_motifs():
    chunks = chunk_documents(_decision_pages())
    dispositif = next(c for c in chunks if c.article_number == "DISPOSITIF")
    assert "PAR CES MOTIFS" in dispositif.text
    assert "Rejette" in dispositif.text
