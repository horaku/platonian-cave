from copy import deepcopy

from doc3_executor.capabilities.ledger_interpreter import interpret_ledger
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.schemas.models import RunState


def _run_to_phase7():
    rs = RunState(run_id="run_f8i", trace_id="trace_f8i")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    hid = rs.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
    run_phase6(
        rs,
        [
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
        ],
    )
    run_phase7(rs)
    return rs


def test_f8i_core_functionality():
    rs = _run_to_phase7()
    view = interpret_ledger(rs)
    assert view["run_id"] == rs.run_id
    assert set(view["claims_by_status"].keys()) == {"proposed", "accepted", "rejected", "needs_review", "verified"}
    assert view["source_link_index"]
    assert view["synthesis_readiness"]["authoritative_ready"] is False


def test_f8i_readonly_invariant():
    rs = _run_to_phase7()
    before = deepcopy(rs)
    _ = interpret_ledger(rs)
    assert rs == before


def test_f8i_contradiction_visibility():
    rs = _run_to_phase7()
    claim = rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]
    claim["contradictions"] = ["claim_other"]
    view = interpret_ledger(rs)
    assert view["open_contradictions"]
    assert view["open_contradictions"][0]["status"] == "open"


def test_f8i_readiness_blockers():
    rs = _run_to_phase7()
    claim = rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]
    claim["validation_status"]["factual_consistency"] = "disputed"
    view = interpret_ledger(rs)
    assert view["synthesis_readiness"]["authoritative_ready"] is False
    assert view["synthesis_readiness"]["blocking_reasons"]

