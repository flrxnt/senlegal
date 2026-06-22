"""Glossaire des termes juridiques du droit sénégalais.

Les termes courants ne figurent pas toujours tels quels dans les textes
officiels (qui utilisent la forme juridique précise). Pour qu'un utilisateur
puisse écrire « garde des enfants » et obtenir l'article qui traite de la
« puissance paternelle », on enrichit la requête avant l'embedding.
"""
from __future__ import annotations

import re

# Termes courants → forme juridique / synonyme développé.
ACRONYMS: dict[str, str] = {
    "garde des enfants": "puissance paternelle droit de garde",
    "autorité parentale": "puissance paternelle",
    "pension": "obligation alimentaire pension alimentaire",
    "héritage": "succession ab intestat dévolution successorale",
    "dot": "régime dotal régime matrimonial",
    "mariage religieux": "constatation du mariage célébration",
    "polygamie": "option de polygamie limitation de monogamie",
    "tuteur": "tutelle juge des tutelles conseil de famille",
    "adoption": "adoption plénière adoption limitée",
    "divorce": "dissolution du mariage divorce contentieux consentement mutuel",
    "séparation": "séparation de corps effets de la séparation",
    "nom de famille": "nom patronymique attribution du nom",
    "état civil": "officier de l'état civil actes registres",
    "absent": "absence disparition présomption d'absence",
    "émancipation": "émancipation mineur capacité juridique",
    "curatelle": "majeur en curatelle incapable majeur protégé",
    "testament": "testament olographe testament authentique legs",
    "donation": "donation entre vifs libéralité irrévocabilité",
    "succession musulmane": "succession de droit musulman légitimaire héritier universel",
    "réserve héréditaire": "réserve quotité disponible réduction",
    "partage": "partage successoral indivision liquidation",
    "filiation": "filiation légitime filiation naturelle désaveu de paternité",
    "reconnaissance": "reconnaissance de paternité filiation paternelle",
    "régime matrimonial": "séparation de biens régime dotal communauté",
}


def expand_query(query: str) -> str:
    """Renvoie la requête éventuellement augmentée des formes juridiques des termes trouvés."""
    expansions: list[str] = []
    for terme, forme in ACRONYMS.items():
        if re.search(rf"\b{re.escape(terme)}\b", query, flags=re.IGNORECASE):
            expansions.append(forme)
    if not expansions:
        return query
    return query + " " + " ".join(expansions)
