from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase2_gate import review_phase2
from doc3_executor.phases.vocabulary_bootstrap import build_vocabulary_candidates
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id


PHASE1_KEY = "phase1_intent_surface"
PHASE2_KEY = "phase2_vocabulary_bootstrap"


def run_phase2(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    phase1_surface = store.read_promoted(PHASE1_KEY)
    if not phase1_surface:
        raise ValueError("phase2 requires promoted phase1_intent_surface")

    vocab = build_vocabulary_candidates(phase1_surface)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE2_KEY,
        payload=asdict(vocab),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    decision, reason = review_phase2(proposal.payload)
    store.add_event(
        DecisionEvent(
            record_id=proposal.record_id,
            decision=decision,
            reason=reason,
            phase=PHASE2_KEY,
        )
    )
    if decision.value == "PROMOTE":
        store.promote(PHASE2_KEY, proposal)
    return run_state


def is_phase2_invalidated(run_state: RunState) -> bool:
    phase1 = run_state.promoted.get(PHASE1_KEY)
    phase2 = run_state.promoted.get(PHASE2_KEY)
    if not phase1 or not phase2:
        return False

    expected = build_vocabulary_candidates(phase1).phase1_fingerprint
    return phase2.get("phase1_fingerprint") != expected
