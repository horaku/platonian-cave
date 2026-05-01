from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from doc3_executor.schemas.models import DecisionEvent, GateDecision, RunState


ALLOWED_CAPABILITIES_BY_PHASE: Dict[str, List[str]] = {
    "phase1_intent_surface": ["state.read", "intent.extract"],
    "phase2_vocabulary_bootstrap": ["state.read", "vocabulary.bootstrap"],
    "phase3_terminology_normalization": ["state.read", "terminology.normalize"],
    "phase4_hypothesis_lattice": ["state.read", "hypothesis.generate"],
    "phase5_source_discovery_design": ["state.read", "discovery.design"],
    "phase6_triage_and_extraction": ["state.read", "source.fetch", "extract.claims"],
    "phase7_verification_memory": ["state.read", "validate.claim", "compare.contradictions"],
    "phase8_finalizer": ["state.read", "report.render"],
}


@dataclass
class AgentStepRecord:
    step_id: str
    phase: str
    selected_capability: str
    intent_for_step: str
    why_this_step: str
    expected_state_change: str
    risk_flags: List[str] = field(default_factory=list)
    policy_compliant: bool = True


def create_agent_step_record(
    *,
    run_state: RunState,
    step_id: str,
    phase: str,
    selected_capability: str,
    intent_for_step: str,
    why_this_step: str,
    expected_state_change: str,
    risk_flags: List[str] | None = None,
) -> AgentStepRecord:
    allowed = ALLOWED_CAPABILITIES_BY_PHASE.get(phase, [])
    compliant = selected_capability in allowed
    step = AgentStepRecord(
        step_id=step_id,
        phase=phase,
        selected_capability=selected_capability,
        intent_for_step=intent_for_step,
        why_this_step=why_this_step,
        expected_state_change=expected_state_change,
        risk_flags=risk_flags or [],
        policy_compliant=compliant,
    )

    run_state.promoted.setdefault("agent_runtime", {})
    run_state.promoted["agent_runtime"].setdefault("agent_step_records", []).append(asdict(step))

    reason = "agent capability allowed for phase"
    decision = GateDecision.PROMOTE
    if not compliant:
        reason = f"policy violation: capability '{selected_capability}' is not allowed in {phase}"
        decision = GateDecision.REJECT

    run_state.events.append(
        DecisionEvent(
            record_id=step_id,
            decision=decision,
            reason=reason,
            phase=phase,
        )
    )
    return step


def step_decision_audit_chain(run_state: RunState, step_id: str) -> Dict[str, object]:
    records = run_state.promoted.get("agent_runtime", {}).get("agent_step_records", [])
    step = next((r for r in records if r["step_id"] == step_id), None)
    event = next((e for e in run_state.events if e.record_id == step_id), None)
    return {
        "step_record": step,
        "decision_event": asdict(event) if event else None,
        "promoted_state_snapshot": dict(run_state.promoted),
    }
