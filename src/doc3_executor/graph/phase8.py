from __future__ import annotations

from doc3_executor.gates.phase8_gate import review_phase8
from doc3_executor.graph.phase7 import PHASE7_KEY, ready_for_authoritative_synthesis
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE8_KEY = "phase8_finalizer"


def run_phase8(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    p7 = store.read_promoted(PHASE7_KEY)
    if not p7:
        raise ValueError("phase8 requires promoted phase7_verification_memory")

    ledger = p7.get("verification_ledger", {})
    claims = ledger.get("claim_records", [])
    contradictions = [c for c in claims if c.get("contradictions")]
    authoritative_ready = ready_for_authoritative_synthesis(run_state)
    has_disputed = any("disputed" in c.get("validation_status", {}).values() for c in claims)

    limitations = []
    next_actions = []
    if authoritative_ready and not contradictions and not has_disputed:
        outcome = "authoritative_synthesis"
        report_type = "authoritative"
        filename = "authoritative_synthesis_report.md"
        main = "Authoritative synthesis produced from validated evidence core."
        finalization_status = "authoritative"
    elif claims:
        outcome = "limited_synthesis"
        report_type = "limited"
        filename = "limited_synthesis_report.md"
        main = "Limited synthesis produced with explicit limitations."
        limitations = [
            "Some claims remain unchecked and/or unverified; conclusions are scoped to validated subset only.",
        ]
        next_actions = [
            "Validate unchecked claim fields (factual/citation/semantic).",
            "Review unresolved contradictions before authoritative finalization.",
        ]
        finalization_status = "limited"
    else:
        outcome = "blocked_finalization_report"
        report_type = "blocked"
        filename = "blocked_finalization_report.md"
        main = "No synthesis was produced because finalization is blocked."
        limitations = ["No claim corpus is available for synthesis."]
        next_actions = ["Populate verification ledger claim records and rerun finalization."]
        finalization_status = "blocked"

    if has_disputed:
        outcome = "blocked_finalization_report"
        report_type = "blocked"
        filename = "blocked_finalization_report.md"
        main = "No synthesis was produced because finalization is blocked."
        limitations = ["At least one claim has disputed validation status."]
        next_actions = ["Resolve disputed validations before finalization."]
        finalization_status = "blocked"

    payload = {
        "finalization": {
            "outcome": outcome,
            "finalization_status": finalization_status,
            "claim_records": claims,
            "open_contradictions": contradictions,
            "limitations": limitations,
            "next_actions": next_actions,
            "report": {
                "report_type": report_type,
                "report_filename": filename,
                "main_synthesis": main,
            },
        }
    }

    proposal = ProposalRecord(record_id=new_id("proposal"), phase=PHASE8_KEY, payload=payload, trace_id=run_state.trace_id)
    store.propose(proposal)
    decision, reason = review_phase8(payload)
    store.add_event(DecisionEvent(record_id=proposal.record_id, decision=decision, reason=reason, phase=PHASE8_KEY))
    if decision.value == "PROMOTE":
        store.promote(PHASE8_KEY, proposal)
    return run_state
