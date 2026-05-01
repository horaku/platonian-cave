from __future__ import annotations

from doc3_executor.schemas.models import GateDecision


def review_phase8(payload: dict):
    finalization = payload.get("finalization")
    if not finalization:
        return GateDecision.REJECT, "missing finalization payload"

    outcome = finalization.get("outcome")
    if outcome not in {"authoritative_synthesis", "limited_synthesis", "blocked_finalization_report"}:
        return GateDecision.REVISE, "invalid phase8 outcome"

    report = finalization.get("report", {})
    if not report.get("report_type") or not report.get("report_filename"):
        return GateDecision.REVISE, "missing report metadata"

    claims = finalization.get("claim_records", [])
    if not claims:
        return GateDecision.REVISE, "missing claim records for finalization"

    has_unchecked = False
    has_disputed = False
    for claim in claims:
        vs = claim.get("validation_status", {})
        values = list(vs.values())
        has_unchecked = has_unchecked or ("unchecked" in values)
        has_disputed = has_disputed or ("disputed" in values)

    if outcome == "authoritative_synthesis" and (has_unchecked or has_disputed):
        return GateDecision.REVISE, "authoritative synthesis requires fully validated non-disputed claims"

    if outcome == "limited_synthesis":
        if not finalization.get("limitations"):
            return GateDecision.REVISE, "limited synthesis requires explicit limitations disclosure"

    if outcome == "blocked_finalization_report":
        main = report.get("main_synthesis", "")
        if "No synthesis was produced because finalization is blocked." not in main:
            return GateDecision.REVISE, "blocked report must state that synthesis was not produced"
        if not finalization.get("next_actions"):
            return GateDecision.REVISE, "blocked report requires actionable next steps"

    return GateDecision.PROMOTE, "phase8 finalizer satisfies terminal gate"
