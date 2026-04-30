from __future__ import annotations

from doc3_executor.schemas.models import GateDecision


def review_phase2(vocabulary_payload: dict):
    fragments = vocabulary_payload.get("by_surface_fragment", [])
    if not fragments:
        return GateDecision.REJECT, "no fragments in vocabulary payload"

    for fragment in fragments:
        terms = fragment.get("candidate_professional_terms", [])
        if not terms:
            return GateDecision.REVISE, "no candidate terms for fragment"

        # phase2 gate: no preferred-term normalization yet
        if "preferred_term" in fragment:
            return GateDecision.REVISE, "premature normalization detected"

        if not fragment.get("nearby_but_confusable_terms"):
            return GateDecision.REVISE, "missing confusable terms"

        if not fragment.get("unresolved_terminology_questions"):
            return GateDecision.REVISE, "missing unresolved terminology questions"

    return GateDecision.PROMOTE, "phase2 payload satisfies expansion-only contract"
