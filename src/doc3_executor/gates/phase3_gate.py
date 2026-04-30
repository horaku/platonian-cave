from __future__ import annotations

from doc3_executor.schemas.models import GateDecision

VALID_ROLES = {"seed", "expansion", "negative_filter", "context_only"}


def review_phase3(lexicon_payload: dict):
    families = lexicon_payload.get("term_families", [])
    if not families:
        return GateDecision.REJECT, "no term families"

    seen_preferred = set()
    for family in families:
        pref = family.get("preferred_term")
        if not pref:
            return GateDecision.REJECT, "missing preferred term"
        if pref in seen_preferred:
            return GateDecision.REVISE, "duplicate preferred term families"
        seen_preferred.add(pref)

        if family.get("retrieval_role") not in VALID_ROLES:
            return GateDecision.REVISE, "invalid retrieval role"

        reason = family.get("why_preferred_for_this_workflow", "")
        if not reason:
            return GateDecision.REVISE, "missing reason for preferred term"

        reason_lower = reason.lower()
        if not ("retrieval" in reason_lower or "precision" in reason_lower or "fidelity" in reason_lower):
            return GateDecision.REVISE, "preferred term reason not tied to retrieval precision/fidelity"

        if not family.get("source_terms"):
            return GateDecision.REVISE, "orphan preferred term not linked to phase2 candidates"

    return GateDecision.PROMOTE, "phase3 lexicon satisfies normalization gate"
