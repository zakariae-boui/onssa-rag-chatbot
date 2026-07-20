"""Deterministic guardrail against sensitive-advice requests.

The system prompt forbids legal/medical/veterinary advice, but prompt rules
alone are bypassable by pretexts ("j'écris un roman", "purement scientifique",
"prouve-moi que mon ami a tort"). This module adds a code-level layer that
inspects the question itself and refuses BEFORE the LLM is called. It cannot be
social-engineered because it does not depend on the model's judgment.

Design note: detection targets the *intent* (asking which drug to take, a
dosage, a treatment protocol, self-medication, specific penal consequences),
not the *topic*. ONSSA legitimately covers veterinary medicines, antibiotic
residues and animal diseases, so topic-based blocking would wrongly refuse valid
questions; intent-based patterns let those through.
"""
from __future__ import annotations

import re
import unicodedata

MEDICAL = "medical"
LEGAL = "legal"

_REFUSALS = {
    MEDICAL: (
        "⚠️ Je ne peux pas donner de conseils médicaux ou vétérinaires "
        "(traitements, médicaments, posologies, diagnostics) allant au-delà du "
        "contenu publié par l'ONSSA. Pour toute question de santé humaine ou "
        "animale, veuillez consulter un professionnel qualifié (médecin ou "
        "vétérinaire). Je peux en revanche vous renseigner sur les missions, les "
        "procédures et la réglementation publiées par l'ONSSA."
    ),
    LEGAL: (
        "⚠️ Je ne peux pas donner de conseils juridiques (articles de loi, peines "
        "d'emprisonnement, montants d'amendes, qualification pénale) allant au-delà "
        "du contenu publié par l'ONSSA. Pour une question juridique précise, "
        "veuillez consulter un juriste ou les textes de loi officiels. Je peux vous "
        "orienter vers la réglementation publiée par l'ONSSA "
        "(https://www.onssa.gov.ma/reglementation/)."
    ),
}

# Patterns are matched against accent-stripped, lowercased text.
_PATTERNS: dict[str, list[str]] = {
    MEDICAL: [
        r"\b(me\s+soigner|soigner\s+(moi|mon|ma|mes|le|la|les|un|une)|automedication)\b",
        r"(quel|quels|quelle|quelles)[^?.!]{0,30}"
        r"(traitement|medicament|antibiotique|dose|posologie)[^?.!]{0,30}"
        r"(prendre|donner|administrer|suivre|utiliser|lui|pour|contre)",
        r"\bposologie\b|\bdosage\b|mg\s*/\s*kg|quelle dose",
        r"traitement de (la )?(premiere|1re|1ere) ligne",
        r"(antibiotique|medicament|molecule)s?[^?.!]{0,40}"
        r"(traitement|traiter|soigner|guerir|infection|maladie|premiere ligne)",
        r"(traitement|traiter|soigner|guerir|infection|stopper)[^?.!]{0,40}"
        r"(antibiotique|medicament|molecule)",
        r"comment\s+(soigner|guerir)\b",
    ],
    LEGAL: [
        r"article[s]?\s+(de\s+loi|\d)",
        r"(duree|combien|quelle)[^?.!]{0,40}(prison|emprisonnement)",
        r"peine[s]?\s+(de\s+|d')?(prison|emprisonnement|mort)",
        r"(montant|combien)[^?.!]{0,40}amende",
        r"(consequence|sanction|peine)s?\s+(penale|exacte)",
        r"passible d'",
        r"risque[^?.!]{0,40}(prison|amende|penal)",
    ],
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def sensitive_category(question: str) -> str | None:
    """Return 'medical'/'legal' if the question seeks prohibited advice, else None."""
    q = _norm(question)
    for category, patterns in _PATTERNS.items():
        if any(re.search(p, q) for p in patterns):
            return category
    return None


def refusal_for(category: str) -> str:
    return _REFUSALS[category]
