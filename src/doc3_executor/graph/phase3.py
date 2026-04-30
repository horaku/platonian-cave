from __future__ import annotations

from dataclasses import asdict

from doc3_executor.gates.phase3_gate import review_phase3
from doc3_executor.phases.terminology_normalization import normalize_terminology
from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState
from doc3_executor.state.store import InMemoryStateStore
from doc3_executor.utils.ids import new_id

PHASE2_KEY = "phase2_vocabulary_bootstrap"
PHASE3_KEY = "phase3_terminology_normalization"


def run_phase3(run_state: RunState) -> RunState:
    store = InMemoryStateStore(run_state)
    phase2_vocab = store.read_promoted(PHASE2_KEY)
    if not phase2_vocab:
        raise ValueError("phase3 requires promoted phase2_vocabulary_bootstrap")

    lexicon = normalize_terminology(phase2_vocab)
    proposal = ProposalRecord(
        record_id=new_id("proposal"),
        phase=PHASE3_KEY,
        payload=asdict(lexicon),
        trace_id=run_state.trace_id,
    )
    store.propose(proposal)

    decision, reason = review_phase3(proposal.payload)
    store.add_event(
        DecisionEvent(
            record_id=proposal.record_id,
            decision=decision,
            reason=reason,
            phase=PHASE3_KEY,
        )
    )
    if decision.value == "PROMOTE":
        store.promote(PHASE3_KEY, proposal)

    return run_state
