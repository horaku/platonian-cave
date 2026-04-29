from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Confidence(str, Enum):
    STABLE = "stable"
    TENTATIVE = "tentative"
    SPECULATIVE = "speculative"


class AssumptionStatus(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    RISKY = "risky"


class GateDecision(str, Enum):
    PROMOTE = "PROMOTE"
    REVISE = "REVISE"
    REJECT = "REJECT"


@dataclass
class CandidateInterpretation:
    interpretation: str
    confidence: Confidence
    missing_information: List[str] = field(default_factory=list)


@dataclass
class LatentAssumption:
    assumption: str
    status: AssumptionStatus


@dataclass
class ProblemSurfaceRecord:
    stated_request: str
    user_goal: Optional[str]
    stated_constraints: List[str]
    unresolved_slots: List[str]
    ambiguities: List[str]
    candidate_interpretations: List[CandidateInterpretation]
    latent_assumptions: List[LatentAssumption]
    prohibited_moves: List[str]


@dataclass
class ProposalRecord:
    record_id: str
    phase: str
    payload: Dict
    trace_id: str


@dataclass
class DecisionEvent:
    record_id: str
    decision: GateDecision
    reason: str
    phase: str


@dataclass
class RunState:
    run_id: str
    trace_id: str
    proposals: List[ProposalRecord] = field(default_factory=list)
    promoted: Dict[str, Dict] = field(default_factory=dict)
    events: List[DecisionEvent] = field(default_factory=list)
