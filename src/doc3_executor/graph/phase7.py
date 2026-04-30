from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase7_gate import review_phase7
from doc3_executor.phases.verification_memory import build_verification_ledger
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE6_KEY = "phase6_triage_and_extraction"
PHASE7_KEY = "phase7_verification_memory"


def run_phase7(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    phase6 = store.read_promoted(PHASE6_KEY)
    if not phase6:
        raise ValueError("phase7 requires promoted phase6_triage_and_extraction")

    ledger = build_verification_ledger(run_state.promoted, phase6, run_state.run_id)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE7_KEY,
        payload=asdict(ledger),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    decision, reason = review_phase7(proposal.payload)
    store.add_event(DecisionEvent(record_id=proposal.record_id, decision=decision, reason=reason, phase=PHASE7_KEY))
    if decision.value == "PROMOTE":
        store.promote(PHASE7_KEY, proposal)
    return run_state


def ready_for_authoritative_synthesis(run_state: RunState) -> bool:
    p7 = run_state.promoted.get(PHASE7_KEY)
    if not p7:
        return False
    for c in p7.get("verification_ledger", {}).get("claim_records", []):
        vs = c.get("validation_status", {})
        if "unchecked" in vs.values():
            return False
    return True
