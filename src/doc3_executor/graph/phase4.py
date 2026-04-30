from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase4_gate import review_phase4
from doc3_executor.phases.hypothesis_lattice import build_hypothesis_lattice
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE1_KEY = "phase1_intent_surface"
PHASE3_KEY = "phase3_terminology_normalization"
PHASE4_KEY = "phase4_hypothesis_lattice"


def run_phase4(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    phase1 = store.read_promoted(PHASE1_KEY)
    phase3 = store.read_promoted(PHASE3_KEY)
    if not phase1 or not phase3:
        raise ValueError("phase4 requires promoted phase1_intent_surface and phase3_terminology_normalization")

    lattice = build_hypothesis_lattice(phase1, phase3)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE4_KEY,
        payload=asdict(lattice),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    decision, reason = review_phase4(proposal.payload)
    store.add_event(
        DecisionEvent(
            record_id=proposal.record_id,
            decision=decision,
            reason=reason,
            phase=PHASE4_KEY,
        )
    )
    if decision.value == "PROMOTE":
        store.promote(PHASE4_KEY, proposal)

    return run_state
