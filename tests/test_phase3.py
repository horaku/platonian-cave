from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.schemas.models import GateDecision, RunState


def _run_to_phase3():
    rs = RunState(run_id="run_f3", trace_id="trace_f3")
    run_phase1(rs, "Хочу понять, как лучше искать материалы про то, почему люди бросают сложные онлайн-курсы")
    run_phase2(rs)
    run_phase3(rs)
    return rs


def test_f3_core_functionality():
    rs = _run_to_phase3()
    proposal = rs.proposals[-1]
    assert proposal.phase == "phase3_terminology_normalization"
    families = proposal.payload["term_families"]
    assert families
    assert all("preferred_term" in f for f in families)
    assert all("retrieval_role" in f for f in families)


def test_f3_gate_invariants_reason_tied_to_retrieval_or_fidelity():
    rs = _run_to_phase3()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["term_families"][0]["why_preferred_for_this_workflow"] = "просто красивый термин"

    from doc3_executor.gates.phase3_gate import review_phase3

    decision, reason = review_phase3(payload)
    assert decision == GateDecision.REVISE
    assert "retrieval precision/fidelity" in reason


def test_f3_crossphase_compatibility_orphan_terms_rejected():
    rs = _run_to_phase3()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["term_families"][0]["source_terms"] = []

    from doc3_executor.gates.phase3_gate import review_phase3

    decision, reason = review_phase3(payload)
    assert decision == GateDecision.REVISE
    assert "orphan" in reason
