from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class WorkingLexiconResult:
    term_families: List[Dict]
    source_phase2_fingerprint: str


def _fingerprint_phase2(vocabulary_payload: Dict) -> str:
    key_parts = []
    for fragment in vocabulary_payload.get("by_surface_fragment", []):
        for term in fragment.get("candidate_professional_terms", []):
            key_parts.append(term.get("term", ""))
    return str(abs(hash("|".join(sorted(key_parts)))))


def normalize_terminology(vocabulary_payload: Dict) -> WorkingLexiconResult:
    frag = vocabulary_payload["by_surface_fragment"][0]
    terms = [t["term"] for t in frag.get("candidate_professional_terms", [])]

    families = [
        {
            "family_id": "f_dropout",
            "preferred_term": "dropout",
            "acceptable_synonyms": ["attrition", "non-completion"],
            "terms_to_avoid": [{"term": "churn", "reason": "маркетинговый контекст"}],
            "definition_snippet": "Прекращение прохождения курса до завершения.",
            "conflict_notes": ["иногда смешивается с non-completion"],
            "why_preferred_for_this_workflow": "точнее для retrieval причин прекращения обучения",
            "retrieval_role": "seed",
            "source_terms": [t for t in terms if t in {"dropout", "persistence", "retention"}],
        },
        {
            "family_id": "f_retention",
            "preferred_term": "retention",
            "acceptable_synonyms": ["persistence"],
            "terms_to_avoid": [{"term": "engagement", "reason": "слишком широкий поведенческий термин"}],
            "definition_snippet": "Удержание обучающихся в процессе курса.",
            "conflict_notes": ["может требовать разделения с engagement"],
            "why_preferred_for_this_workflow": "полезен для precision при поиске факторов удержания",
            "retrieval_role": "expansion",
            "source_terms": [t for t in terms if t in {"retention", "learner engagement", "persistence"}],
        },
        {
            "family_id": "f_ir",
            "preferred_term": "information retrieval",
            "acceptable_synonyms": ["literature search"],
            "terms_to_avoid": [{"term": "google search", "reason": "слишком общий и неоднозначный"}],
            "definition_snippet": "Методы и практики системного поиска источников.",
            "conflict_notes": [],
            "why_preferred_for_this_workflow": "повышает instruction fidelity для проектирования search strategy",
            "retrieval_role": "context_only",
            "source_terms": [t for t in terms if t in {"information retrieval"}],
        },
    ]

    return WorkingLexiconResult(term_families=families, source_phase2_fingerprint=_fingerprint_phase2(vocabulary_payload))
