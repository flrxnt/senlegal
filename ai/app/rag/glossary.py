"""Glossaire des acronymes du droit sénégalais de la commande publique.

Les sigles ne figurent presque jamais tels quels dans les textes officiels
(qui utilisent la forme développée). Pour qu'un utilisateur puisse écrire
"DRP" et obtenir l'article qui définit la « demande de renseignements et
de prix », on enrichit la requête avant l'embedding.
"""
from __future__ import annotations

import re

# Sigles → forme développée (en minuscules, sans accents superflus).
ACRONYMS: dict[str, str] = {
    "DRP": "demande de renseignements et de prix",
    "DRPR": "demande de renseignements et de prix à compétition restreinte",
    "DRPO": "demande de renseignements et de prix ouverte",
    "AAO": "appel d'offres",
    "AOO": "appel d'offres ouvert",
    "AOR": "appel d'offres restreint",
    "AOI": "appel d'offres international",
    "AON": "appel d'offres national",
    "DAO": "dossier d'appel d'offres",
    "DPAO": "données particulières de l'appel d'offres",
    "CCAG": "cahier des clauses administratives générales",
    "CCAP": "cahier des clauses administratives particulières",
    "CCTG": "cahier des clauses techniques générales",
    "CCTP": "cahier des clauses techniques particulières",
    "ARCOP": "Autorité de Régulation de la Commande Publique",
    "ARMP": "Autorité de Régulation des Marchés Publics",
    "DCMP": "Direction Centrale des Marchés Publics",
    "CRD": "Comité de Règlement des Différends",
    "CMP": "Code des Marchés Publics",
    "PPM": "plan de passation des marchés",
    "PV": "procès-verbal",
    "MOD": "maîtrise d'ouvrage déléguée",
    "PPP": "partenariat public-privé",
    "UNAPPP": "Unité Nationale d'Appui aux Partenariats Public-Privé",
    "BOAMP": "Bulletin Officiel des Marchés Publics",
    "ANO": "avis de non-objection",
    "OS": "ordre de service",
    "RC": "règlement de la consultation",
    "DQE": "détail quantitatif et estimatif",
    "BPU": "bordereau des prix unitaires",
}


def expand_query(query: str) -> str:
    """Renvoie la requête éventuellement augmentée des formes développées des sigles trouvés."""
    expansions: list[str] = []
    for sigle, forme in ACRONYMS.items():
        # Sigle isolé (frontières \b), insensible à la casse.
        if re.search(rf"\b{re.escape(sigle)}\b", query, flags=re.IGNORECASE):
            expansions.append(forme)
    if not expansions:
        return query
    return query + " " + " ".join(expansions)
