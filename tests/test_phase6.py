from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import can_run_synthesis, run_phase6
from doc3_executor.schemas.models import GateDecision, RunState


def _records(active_hypothesis_id: str):
    return [
        {
            "source_id": "s1",
            "linked_hypotheses": [active_hypothesis_id],
            "url_or_doi": "https://example.org/s1",
            "section": "results",
            "span": "p3",
            "claim": "Higher cognitive load increases dropout risk.",
            "evidence_type": "case_study",
            "supports_or_challenges": "supports",
        },
        {"source_id": "s2", "linked_hypotheses": [], "url_or_doi": "https://example.org/s2"},
    ]


def _run_to_phase6():
    rs = RunState(run_id="run_f6", trace_id="trace_f6")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    hid = rs.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
    run_phase6(rs, _records(hid))
    return rs


def test_f6_core_functionality():
    rs = _run_to_phase6()
    proposal = rs.proposals[-1]
    assert proposal.phase == "phase6_triage_and_extraction"
    assert proposal.payload["triage"]["accepted_items"]
    assert proposal.payload["extractions"]


def test_f6_gate_invariants_extraction_required_for_accepted_items():
    rs = _run_to_phase6()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["extractions"] = []

    from doc3_executor.gates.phase6_gate import review_phase6

    active_ids = [h["hypothesis_id"] for h in rs.promoted["phase4_hypothesis_lattice"]["hypotheses"]]
    decision, reason = review_phase6(payload, active_ids)
    assert decision == GateDecision.REVISE
    assert "extraction matrix" in reason


def test_f6_crossphase_compatibility_active_hypothesis_linking():
    rs = _run_to_phase6()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["extractions"][0]["linked_hypothesis"] = "unknown_hypothesis"

    from doc3_executor.gates.phase6_gate import review_phase6

    active_ids = [h["hypothesis_id"] for h in rs.promoted["phase4_hypothesis_lattice"]["hypotheses"]]
    decision, reason = review_phase6(payload, active_ids)
    assert decision == GateDecision.REVISE
    assert "non-active hypothesis" in reason


def test_f6_policy_block_synthesis_before_phase6_promoted():
    rs = RunState(run_id="run_f6_gate", trace_id="trace_f6_gate")
    run_phase1(rs, "Нужен план поиска")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    assert can_run_synthesis(rs) is False
