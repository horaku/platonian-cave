from __future__ import annotations

from doc3_executor.schemas.models import (
    AssumptionStatus,
    CandidateInterpretation,
    Confidence,
    LatentAssumption,
    ProblemSurfaceRecord,
)


AMBIGUITY_MARKERS = ["лучше", "почему", "как", "оптимально"]


def extract_problem_surface(user_input: str) -> ProblemSurfaceRecord:
    text = user_input.strip()
    ambiguities = [m for m in AMBIGUITY_MARKERS if m in text.lower()]

    interpretation = CandidateInterpretation(
        interpretation="Исследовательский запрос о факторах и методах поиска по теме.",
        confidence=Confidence.TENTATIVE,
        missing_information=[
            "Целевая аудитория/контекст",
            "Ограничения по времени/языку/типам источников",
        ],
    )
    assumptions = [
        LatentAssumption(
            assumption="Пользователь хочет построить исследовательский workflow, а не готовый список источников.",
            status=AssumptionStatus.INFERRED,
        )
    ]
    return ProblemSurfaceRecord(
        stated_request=text,
        user_goal=None,
        stated_constraints=[],
        unresolved_slots=interpretation.missing_information,
        ambiguities=ambiguities,
        candidate_interpretations=[interpretation],
        latent_assumptions=assumptions,
        prohibited_moves=[
            "no_solution_hypotheses",
            "no_domain_lock_in",
            "no_unlabeled_specialist_terms",
        ],
    )
