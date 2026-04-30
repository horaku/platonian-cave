from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import ready_for_authoritative_synthesis, run_phase7
from doc3_executor.schemas.models import GateDecision, RunState


def _run_to_phase7():
    rs = RunState(run_id="run_f7", trace_id="trace_f7")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    hid = rs.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
    run_phase6(rs, [
        {
            "source_id": "s1",
            "linked_hypotheses": [hid],
            "url_or_doi": "https://example.org/s1",
            "section": "results",
            "span": "p3",
            "claim": "Higher cognitive load increases dropout risk.",
            "evidence_type": "case_study",
            "supports_or_challenges": "supports",
        }
    ])
    run_phase7(rs)
    return rs


def test_f7_core_functionality():
    rs = _run_to_phase7()
    proposal = rs.proposals[-1]
    assert proposal.phase == "phase7_verification_memory"
    ledger = proposal.payload["verification_ledger"]
    assert ledger["run_id"] == rs.run_id
    assert ledger["claim_records"]


def test_f7_gate_invariants_source_links_required():
    rs = _run_to_phase7()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["verification_ledger"]["claim_records"][0]["source_links"] = []

    from doc3_executor.gates.phase7_gate import review_phase7

    decision, reason = review_phase7(payload)
    assert decision == GateDecision.REVISE
    assert "source links" in reason


def test_f7_crossphase_compatibility_claim_locator_and_history_required():
    rs = _run_to_phase7()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["verification_ledger"]["claim_records"][0]["source_links"][0]["locator"] = ""

    from doc3_executor.gates.phase7_gate import review_phase7

    decision, reason = review_phase7(payload)
    assert decision == GateDecision.REVISE
    assert "source link" in reason


def test_f7_policy_block_authoritative_synthesis_before_validation():
    rs = _run_to_phase7()
    assert ready_for_authoritative_synthesis(rs) is False
