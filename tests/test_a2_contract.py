from doc3_executor.capabilities.agentic_runtime import (
    ALLOWED_CAPABILITIES_BY_PHASE,
    create_agent_step_record,
    step_decision_audit_chain,
)
from doc3_executor.schemas.models import RunState


def test_a2_contract_step_traceability():
    rs = RunState(run_id="run_a21", trace_id="trace_a21")
    step = create_agent_step_record(
        run_state=rs,
        step_id="step_1",
        phase="phase6_triage_and_extraction",
        selected_capability="extract.claims",
        intent_for_step="Extract claim candidates with provenance",
        why_this_step="Need structured evidence before verification",
        expected_state_change="append extraction proposals",
        risk_flags=["possible false-positive extraction"],
    )

    assert step.policy_compliant is True
    chain = step_decision_audit_chain(rs, step.step_id)
    assert chain["step_record"]["selected_capability"] == "extract.claims"
    assert chain["decision_event"]["decision"] == "PROMOTE"
    assert "agent_runtime" in chain["promoted_state_snapshot"]


def test_a2_contract_capability_policy_violation_blocked():
    rs = RunState(run_id="run_a21_violation", trace_id="trace_a21_violation")

    disallowed = "source.fetch"
    assert disallowed not in ALLOWED_CAPABILITIES_BY_PHASE["phase2_vocabulary_bootstrap"]

    step = create_agent_step_record(
        run_state=rs,
        step_id="step_viol_1",
        phase="phase2_vocabulary_bootstrap",
        selected_capability=disallowed,
        intent_for_step="Try to fetch sources too early",
        why_this_step="Simulate policy breach",
        expected_state_change="none",
        risk_flags=["premature retrieval"],
    )

    assert step.policy_compliant is False
    chain = step_decision_audit_chain(rs, step.step_id)
    assert chain["decision_event"]["decision"] == "REJECT"
    assert "policy violation" in chain["decision_event"]["reason"]
