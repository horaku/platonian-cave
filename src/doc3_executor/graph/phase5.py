from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase5_gate import review_phase5
from doc3_executor.phases.source_discovery_design import build_source_discovery_plan
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE3_KEY = "phase3_terminology_normalization"
PHASE4_KEY = "phase4_hypothesis_lattice"
PHASE5_KEY = "phase5_source_discovery_design"


def run_phase5(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    phase3 = store.read_promoted(PHASE3_KEY)
    phase4 = store.read_promoted(PHASE4_KEY)
    if not phase3 or not phase4:
        raise ValueError("phase5 requires promoted phase3_terminology_normalization and phase4_hypothesis_lattice")

    plan = build_source_discovery_plan(phase4, phase3)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE5_KEY,
        payload=asdict(plan),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    active_hypothesis_ids = [h["hypothesis_id"] for h in phase4.get("hypotheses", [])]
    decision, reason = review_phase5(proposal.payload, active_hypothesis_ids)
    store.add_event(DecisionEvent(record_id=proposal.record_id, decision=decision, reason=reason, phase=PHASE5_KEY))
    if decision.value == "PROMOTE":
        store.promote(PHASE5_KEY, proposal)
    return run_state


def can_run_retrieval(run_state: RunState) -> bool:
    return PHASE5_KEY in run_state.promoted
