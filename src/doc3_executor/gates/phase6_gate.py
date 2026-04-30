from __future__ import annotations

from doc3_executor.schemas.models import GateDecision


def review_phase6(payload: dict, active_hypothesis_ids: list[str]):
    triage = payload.get("triage")
    extractions = payload.get("extractions", [])
    if not triage:
        return GateDecision.REJECT, "missing triage"

    sc = triage.get("screening_criteria", {})
    if not sc.get("include_if") or not sc.get("exclude_if") or not sc.get("review_bucket_if"):
        return GateDecision.REVISE, "incomplete screening criteria"

    accepted = triage.get("accepted_items", [])
    if accepted and not extractions:
        return GateDecision.REVISE, "accepted items require extraction matrix"

    active = set(active_hypothesis_ids)
    for item in accepted:
        if not set(item.get("linked_hypotheses", [])).intersection(active):
            return GateDecision.REVISE, "accepted item not linked to active hypotheses"

    for ext in extractions:
        if ext.get("linked_hypothesis") not in active:
            return GateDecision.REVISE, "extraction linked to non-active hypothesis"
        locator = ext.get("source_locator", {})
        if not locator.get("url_or_doi"):
            return GateDecision.REVISE, "missing source locator"
        if not ext.get("extracted_claim"):
            return GateDecision.REVISE, "missing extracted claim"

    return GateDecision.PROMOTE, "phase6 triage/extraction satisfies evidence-core gate"
