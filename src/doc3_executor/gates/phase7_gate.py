from __future__ import annotations

from doc3_executor.schemas.models import GateDecision


VALID_STATUSES = {"proposed", "accepted", "rejected", "needs_review", "verified"}
VALID_CHECK = {"unchecked", "passed", "failed", "disputed"}


def review_phase7(payload: dict):
    ledger = payload.get("verification_ledger")
    if not ledger:
        return GateDecision.REJECT, "missing verification_ledger"

    if not ledger.get("run_id"):
        return GateDecision.REJECT, "missing run_id"

    promoted_state = ledger.get("promoted_state", {})
    required_keys = {"problem_surface_id", "working_lexicon_id", "hypothesis_lattice_id", "source_discovery_plan_id"}
    if not required_keys.issubset(set(promoted_state.keys())):
        return GateDecision.REVISE, "missing promoted_state pointers"

    for claim in ledger.get("claim_records", []):
        if claim.get("status") not in VALID_STATUSES:
            return GateDecision.REVISE, "invalid claim status"
        if not claim.get("source_links"):
            return GateDecision.REVISE, "claim missing source links"
        for sl in claim["source_links"]:
            if not sl.get("source_id") or not sl.get("extraction_id") or not sl.get("locator"):
                return GateDecision.REVISE, "invalid source link"

        vs = claim.get("validation_status", {})
        if any(vs.get(k) not in VALID_CHECK for k in ["factual_consistency", "citation_alignment", "semantic_stability"]):
            return GateDecision.REVISE, "invalid validation status"

        if not claim.get("decision_history"):
            return GateDecision.REVISE, "missing decision history"

    return GateDecision.PROMOTE, "phase7 verification ledger satisfies memory gate"
