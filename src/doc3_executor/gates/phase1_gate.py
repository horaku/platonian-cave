from __future__ import annotations

from doc3_executor.schemas.models import GateDecision, ProblemSurfaceRecord


SPECIALIST_TERMS = {"hci", "psychometrics", "econometrics", "clinical trial"}


def review_phase1(record: ProblemSurfaceRecord):
    if not record.stated_request:
        return GateDecision.REJECT, "empty request"
    if "это задача из" in record.stated_request.lower():
        return GateDecision.REVISE, "domain lock-in detected"

    text = record.stated_request.lower()
    if any(term in text for term in SPECIALIST_TERMS):
        return GateDecision.REVISE, "unlabeled specialist terms in user surface"

    if len(record.candidate_interpretations) == 0:
        return GateDecision.REJECT, "no candidate interpretations"

    return GateDecision.PROMOTE, "phase1 record satisfies gate invariants"
