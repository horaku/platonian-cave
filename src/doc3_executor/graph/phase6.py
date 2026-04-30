from __future__ import annotations

from dataclasses import asdict
from typing import List, Dict

from doc3_executor.gates.phase6_gate import review_phase6
from doc3_executor.phases.triage_extraction import triage_and_extract
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE4_KEY = "phase4_hypothesis_lattice"
PHASE5_KEY = "phase5_source_discovery_design"
PHASE6_KEY = "phase6_triage_and_extraction"


def run_phase6(run_state: RunState, retrieved_records: List[Dict]) -> RunState:
    store = InMemoryStateStore(run_state)
    phase4 = store.read_promoted(PHASE4_KEY)
    phase5 = store.read_promoted(PHASE5_KEY)
    if not phase4 or not phase5:
        raise ValueError("phase6 requires promoted phase4_hypothesis_lattice and phase5_source_discovery_design")

    result = triage_and_extract(retrieved_records, phase5, phase4)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE6_KEY,
        payload=asdict(result),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    active_ids = [h["hypothesis_id"] for h in phase4.get("hypotheses", [])]
    decision, reason = review_phase6(proposal.payload, active_ids)
    store.add_event(DecisionEvent(record_id=proposal.record_id, decision=decision, reason=reason, phase=PHASE6_KEY))
    if decision.value == "PROMOTE":
        store.promote(PHASE6_KEY, proposal)
    return run_state


def can_run_synthesis(run_state: RunState) -> bool:
    p6 = run_state.promoted.get(PHASE6_KEY)
    if not p6:
        return False
    return bool(p6.get("extractions"))
