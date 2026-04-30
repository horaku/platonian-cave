from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase1_gate import review_phase1
from doc3_executor.phases.intent_surface import extract_problem_surface
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id


def run_phase1(run_state: RunState, user_input: str) -> RunState:
    store = InMemoryStateStore(run_state)
    surface = extract_problem_surface(user_input)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase="phase1_intent_surface",
        payload=asdict(surface),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    decision, reason = review_phase1(surface)
    event = DecisionEvent(
        record_id=proposal.record_id,
        decision=decision,
        reason=reason,
        phase=proposal.phase,
    )
    store.add_event(event)
    if decision.value == "PROMOTE":
        store.promote(proposal.phase, proposal)
    return run_state
