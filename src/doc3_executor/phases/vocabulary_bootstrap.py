from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VocabularyBootstrapResult:
    by_surface_fragment: List[Dict]
    phase1_fingerprint: str


def _fingerprint(surface: Dict) -> str:
    key = surface.get("stated_request", "") + "|" + "|".join(surface.get("ambiguities", []))
    return str(abs(hash(key)))


def build_vocabulary_candidates(problem_surface: Dict) -> VocabularyBootstrapResult:
    request = problem_surface.get("stated_request", "")
    fragment_id = "surface_main"

    candidates = [
        {"term": "retention", "confidence": "tentative", "rationale": "часто используется для удержания обучающихся"},
        {"term": "dropout", "confidence": "tentative", "rationale": "соответствует прекращению прохождения"},
        {"term": "persistence", "confidence": "speculative", "rationale": "смежный термин устойчивости в курсе"},
        {"term": "learner engagement", "confidence": "speculative", "rationale": "поведенческий фактор, связанный с удержанием"},
    ]

    if "поиск" in request.lower():
        candidates.append(
            {"term": "information retrieval", "confidence": "tentative", "rationale": "отражает задачу поиска источников"}
        )

    return VocabularyBootstrapResult(
        by_surface_fragment=[
            {
                "fragment_id": fragment_id,
                "candidate_professional_terms": candidates,
                "searchable_paraphrases": [
                    "why learners drop out of online courses",
                    "online course retention factors",
                    "persistence in massive online courses",
                ],
                "nearby_but_confusable_terms": [
                    {"term": "churn", "why_confusable": "маркетинговый термин, не всегда учебный контекст"},
                    {"term": "attrition", "why_confusable": "может относиться к персоналу или популяции"},
                ],
                "unresolved_terminology_questions": [
                    "Нужны ли термины из learning analytics как основной словарь?",
                    "Разделять ли dropout и non-completion как разные явления?",
                ],
            }
        ],
        phase1_fingerprint=_fingerprint(problem_surface),
    )
