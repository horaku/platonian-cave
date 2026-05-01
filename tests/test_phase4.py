from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.schemas.models import GateDecision, RunState


def _run_to_phase4():
    rs = RunState(run_id="run_f4", trace_id="trace_f4")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    return rs


def test_f4_core_functionality():
    rs = _run_to_phase4()
    proposal = rs.proposals[-1]
    assert proposal.phase == "phase4_hypothesis_lattice"
    hypotheses = proposal.payload["hypotheses"]
    assert hypotheses
    assert all(h["do_not_rank_yet"] is True for h in hypotheses)


def test_f4_gate_invariants_non_differentiable_rejected():
    rs = _run_to_phase4()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["hypotheses"][1]["framing"] = payload["hypotheses"][0]["framing"]
    payload["hypotheses"][1]["linked_lexicon_terms"] = payload["hypotheses"][0]["linked_lexicon_terms"]
    payload["hypotheses"][1]["type"] = payload["hypotheses"][0]["type"]

    from doc3_executor.gates.phase4_gate import review_phase4

    decision, reason = review_phase4(payload)
    assert decision == GateDecision.REVISE
    assert "non-differentiable" in reason


def test_f4_crossphase_compatibility_links_required():
    rs = _run_to_phase4()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["hypotheses"][0]["linked_lexicon_terms"] = []

    from doc3_executor.gates.phase4_gate import review_phase4

    decision, reason = review_phase4(payload)
    assert decision == GateDecision.REVISE
    assert "linked_lexicon_terms" in reason
