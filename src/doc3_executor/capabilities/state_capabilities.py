from __future__ import annotations

from doc3_executor.schemas.models import ProposalRecord
from doc3_executor.state.store import InMemoryStateStore


def state_read(store: InMemoryStateStore, phase: str):
    return store.read_promoted(phase)


def state_propose(store: InMemoryStateStore, proposal: ProposalRecord):
    return store.propose(proposal)
