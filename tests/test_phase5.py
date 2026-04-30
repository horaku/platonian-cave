from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import can_run_retrieval, run_phase5
from doc3_executor.schemas.models import GateDecision, RunState


def _run_to_phase5():
    rs = RunState(run_id="run_f5", trace_id="trace_f5")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    return rs


def test_f5_core_functionality():
    rs = _run_to_phase5()
    proposal = rs.proposals[-1]
    assert proposal.phase == "phase5_source_discovery_design"
    by_h = proposal.payload["by_hypothesis"]
    assert by_h and by_h[0]["source_groups"] and by_h[0]["query_families"]


def test_f5_gate_invariants_negative_filters_required():
    rs = _run_to_phase5()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["by_hypothesis"][0]["query_families"][0]["negative_filters"] = []

    from doc3_executor.gates.phase5_gate import review_phase5

    active_ids = [h["hypothesis_id"] for h in rs.promoted["phase4_hypothesis_lattice"]["hypotheses"]]
    decision, reason = review_phase5(payload, active_ids)
    assert decision == GateDecision.REVISE
    assert "negative_filters" in reason


def test_f5_crossphase_compatibility_hypothesis_coverage_and_pre_retrieval_gate():
    rs = _run_to_phase5()
    assert can_run_retrieval(rs) is True

    payload = deepcopy(rs.proposals[-1].payload)
    payload["by_hypothesis"] = payload["by_hypothesis"][1:]

    from doc3_executor.gates.phase5_gate import review_phase5

    active_ids = [h["hypothesis_id"] for h in rs.promoted["phase4_hypothesis_lattice"]["hypotheses"]]
    decision, reason = review_phase5(payload, active_ids)
    assert decision == GateDecision.REVISE
    assert "active hypotheses" in reason


def test_f5_policy_block_retrieval_before_phase5_promoted():
    rs = RunState(run_id="run_f5_gate", trace_id="trace_f5_gate")
    run_phase1(rs, "Нужен план поиска")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    assert can_run_retrieval(rs) is False
