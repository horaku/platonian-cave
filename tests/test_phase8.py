from copy import deepcopy

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.graph.phase8 import run_phase8
from doc3_executor.schemas.models import GateDecision, RunState


def _run_to_phase8():
    rs = RunState(run_id="run_f8", trace_id="trace_f8")
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
    run_phase8(rs)
    return rs


def test_f8_core_functionality():
    rs = _run_to_phase8()
    assert rs.proposals[-1].phase == "phase8_finalizer"
    assert rs.events[-1].phase == "phase8_finalizer"
    assert "phase8_finalizer" in rs.promoted


def test_f8_gate_invariants_authoritative_blocked_when_unchecked():
    rs = _run_to_phase8()
    payload = deepcopy(rs.proposals[-1].payload)
    payload["finalization"]["outcome"] = "authoritative_synthesis"
    from doc3_executor.gates.phase8_gate import review_phase8

    decision, reason = review_phase8(payload)
    assert decision == GateDecision.REVISE
    assert "fully validated" in reason


def test_f8_crossphase_compatibility_full_chain():
    rs = _run_to_phase8()
    assert "phase1_intent_surface" in rs.promoted
    assert "phase2_vocabulary_bootstrap" in rs.promoted
    assert "phase3_terminology_normalization" in rs.promoted
    assert "phase4_hypothesis_lattice" in rs.promoted
    assert "phase5_source_discovery_design" in rs.promoted
    assert "phase6_triage_and_extraction" in rs.promoted
    assert "phase7_verification_memory" in rs.promoted
    assert "phase8_finalizer" in rs.promoted


def test_f8_limited_with_disclosure():
    rs = _run_to_phase8()
    f8 = rs.promoted["phase8_finalizer"]["finalization"]
    assert f8["outcome"] == "limited_synthesis"
    assert f8["limitations"]
    assert f8["next_actions"]
    assert f8["finalization_status"] == "limited"


def test_f8_blocked_finalization_report_for_disputed_claims():
    rs = RunState(run_id="run_f8_blocked", trace_id="trace_f8_blocked")
    run_phase1(rs, "Нужен план поиска")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    hid = rs.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
    run_phase6(
        rs,
        [{
            "source_id": "s1",
            "linked_hypotheses": [hid],
            "url_or_doi": "https://example.org/s1",
            "section": "results",
            "span": "p3",
            "claim": "Higher cognitive load increases dropout risk.",
            "evidence_type": "case_study",
            "supports_or_challenges": "supports",
        }],
    )
    run_phase7(rs)
    rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]["validation_status"][
        "factual_consistency"
    ] = "disputed"
    run_phase8(rs)

    f8 = rs.promoted["phase8_finalizer"]["finalization"]
    assert f8["outcome"] == "blocked_finalization_report"
    assert f8["report"]["main_synthesis"] == "No synthesis was produced because finalization is blocked."
    assert f8["next_actions"]


def test_f8_contradiction_preservation():
    rs = _run_to_phase8()
    claim = rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]
    claim["contradictions"] = ["claim_x"]
    run_phase8(rs)
    contradictions = rs.promoted["phase8_finalizer"]["finalization"]["open_contradictions"]
    assert contradictions
    assert contradictions[0]["contradictions"] == ["claim_x"]


def test_f8_authority_boundary_worker_bypass_rejected():
    from doc3_executor.gates.phase8_gate import review_phase8

    payload = {
        "finalization": {
            "outcome": "authoritative_synthesis",
            "report": {"report_type": "authoritative", "report_filename": "authoritative_synthesis_report.md"},
            "claim_records": [],
        }
    }
    decision, _ = review_phase8(payload)
    assert decision in {GateDecision.REJECT, GateDecision.REVISE}
