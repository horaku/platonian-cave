from __future__ import annotations

from doc3_executor.schemas.models import DecisionEvent, ProposalRecord, RunState


class InMemoryStateStore:
    def __init__(self, run_state: RunState):
        self.run_state = run_state

    def propose(self, proposal: ProposalRecord) -> ProposalRecord:
        self.run_state.proposals.append(proposal)
        return proposal

    def promote(self, phase: str, proposal: ProposalRecord) -> None:
        self.run_state.promoted[phase] = proposal.payload

    def add_event(self, event: DecisionEvent) -> None:
        self.run_state.events.append(event)

    def read_promoted(self, phase: str):
        return self.run_state.promoted.get(phase)
