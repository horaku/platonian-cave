from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from doc3_executor.graph.phase7 import PHASE7_KEY, ready_for_authoritative_synthesis
from doc3_executor.schemas.models import RunState


def interpret_ledger(run_state: RunState) -> Dict:
    p7 = run_state.promoted.get(PHASE7_KEY, {})
    ledger = deepcopy(p7.get("verification_ledger", {}))
    claims = ledger.get("claim_records", [])

    claims_by_status = {
        "proposed": [],
        "accepted": [],
        "rejected": [],
        "needs_review": [],
        "verified": [],
    }
    source_link_index: List[Dict] = []
    open_contradictions: List[Dict] = []
    blocking_reasons: List[str] = []
    next_actions: List[str] = []

    for claim in claims:
        status = claim.get("status", "needs_review")
        if status in claims_by_status:
            claims_by_status[status].append(claim)
        else:
            claims_by_status["needs_review"].append(claim)

        source_link_index.append({"claim_id": claim.get("claim_id"), "source_links": claim.get("source_links", [])})

        vs = claim.get("validation_status", {})
        if "unchecked" in vs.values():
            blocking_reasons.append(f"claim {claim.get('claim_id')} has unchecked validation fields")
        if "disputed" in vs.values():
            blocking_reasons.append(f"claim {claim.get('claim_id')} has disputed validation fields")

        for contradicted_claim_id in claim.get("contradictions", []):
            open_contradictions.append(
                {
                    "claim_id": claim.get("claim_id"),
                    "contradicts": contradicted_claim_id,
                    "status": "open",
                }
            )

    if not claims:
        blocking_reasons.append("no claim records found in verification ledger")

    if open_contradictions:
        next_actions.append("Resolve open contradictions before authoritative synthesis.")
    if any("unchecked" in b or "disputed" in b for b in blocking_reasons):
        next_actions.append("Complete claim validation (factual/citation/semantic) for blocked claims.")
    if not next_actions:
        next_actions.append("No blocking actions detected.")

    return {
        "run_id": ledger.get("run_id", run_state.run_id),
        "claims_by_status": claims_by_status,
        "source_link_index": source_link_index,
        "open_contradictions": open_contradictions,
        "synthesis_readiness": {
            "authoritative_ready": ready_for_authoritative_synthesis(run_state),
            "blocking_reasons": blocking_reasons,
        },
        "next_actions": next_actions,
    }

