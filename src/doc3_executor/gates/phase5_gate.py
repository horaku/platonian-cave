from __future__ import annotations

from doc3_executor.schemas.models import GateDecision

REQUIRED_TYPES = {"definition", "method", "benchmark", "case_study", "implementation_pattern", "critique", "failure_mode"}


def review_phase5(plan_payload: dict, active_hypothesis_ids: list[str]):
    by_hypothesis = plan_payload.get("by_hypothesis", [])
    if not by_hypothesis:
        return GateDecision.REJECT, "no source-discovery entries"

    planned_ids = {e.get("hypothesis_id") for e in by_hypothesis}
    if not set(active_hypothesis_ids).issubset(planned_ids):
        return GateDecision.REVISE, "missing source-discovery plan for active hypotheses"

    for entry in by_hypothesis:
        if not entry.get("source_groups"):
            return GateDecision.REVISE, "missing source_groups"
        if not entry.get("query_families"):
            return GateDecision.REVISE, "missing query_families"

        for qf in entry["query_families"]:
            if not qf.get("negative_filters"):
                return GateDecision.REVISE, "missing negative_filters"
            if not qf.get("search_ready_queries"):
                return GateDecision.REVISE, "missing search_ready_queries"
            e_types = set(qf.get("expected_evidence_types", []))
            if not e_types:
                return GateDecision.REVISE, "missing expected_evidence_types"
            if not e_types.issubset(REQUIRED_TYPES):
                return GateDecision.REVISE, "invalid expected_evidence_types values"

    return GateDecision.PROMOTE, "phase5 source-discovery plan satisfies pre-retrieval gate"
