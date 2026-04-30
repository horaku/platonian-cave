from copy import deepcopy

from doc3_executor.capabilities.ledger_interpreter import interpret_ledger
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import is_phase2_invalidated, run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import can_run_retrieval, run_phase5
from doc3_executor.graph.phase6 import can_run_synthesis, run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.graph.phase8 import run_phase8
from doc3_executor.schemas.models import RunState


def _run_to_phase5(text: str = "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники"):
    rs = RunState(run_id="run_it", trace_id="trace_it")
    run_phase1(rs, text)
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    run_phase5(rs)
    return rs


def _run_to_phase8():
    rs = _run_to_phase5("Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
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


def test_it_a_zero_knowledge_input():
    rs = _run_to_phase5()
    p1 = rs.promoted["phase1_intent_surface"]
    assert p1["candidate_interpretations"]
    assert "phase5_source_discovery_design" in rs.promoted


def test_it_b_no_retrieval_before_design():
    rs = RunState(run_id="run_it_b", trace_id="trace_it_b")
    run_phase1(rs, "Нужен план поиска")
    run_phase2(rs)
    run_phase3(rs)
    run_phase4(rs)
    assert can_run_retrieval(rs) is False


def test_it_c_source_group_separation():
    rs = _run_to_phase5()
    by_h = rs.promoted["phase5_source_discovery_design"]["by_hypothesis"][0]
    groups = by_h["source_groups"]
    assert len(groups) >= 2
    assert all(g.get("epistemic_role") and g.get("limitations") for g in groups)


def test_it_d_contradiction_preservation():
    rs = _run_to_phase8()
    claim = rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]
    claim["contradictions"] = ["claim_other"]
    run_phase8(rs)
    assert rs.promoted["phase8_finalizer"]["finalization"]["open_contradictions"][0]["contradictions"] == ["claim_other"]


def test_it_e_synthesis_refusal_without_provenance():
    rs = _run_to_phase5()
    assert can_run_synthesis(rs) is False


def test_it_f_reference_leakage_guards():
    rs = _run_to_phase5()
    p2 = str(rs.promoted["phase2_vocabulary_bootstrap"]).lower()
    p5 = str(rs.promoted["phase5_source_discovery_design"]).lower()
    assert "pico" not in p2
    assert "boolean only" not in p5


def test_it_g_reopen_and_invalidate_flow():
    rs = _run_to_phase5()
    rs.promoted["phase1_intent_surface"]["stated_request"] = "Новый запрос"
    assert is_phase2_invalidated(rs) is True


def test_it_h_auditability():
    rs = _run_to_phase8()
    assert rs.events
    assert rs.proposals
    assert rs.promoted["phase7_verification_memory"]["verification_ledger"]["run_id"] == rs.run_id


def test_it_i_interpreter_readonly_audit_view():
    rs = _run_to_phase8()
    before = deepcopy(rs)
    view = interpret_ledger(rs)
    assert view["run_id"] == rs.run_id
    assert rs == before


def test_it_j_finalizer_outcome_matrix():
    rs_limited = _run_to_phase8()
    assert rs_limited.promoted["phase8_finalizer"]["finalization"]["outcome"] == "limited_synthesis"

    rs_blocked = _run_to_phase5("Нужен план поиска")
    hid = rs_blocked.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
    run_phase6(
        rs_blocked,
        [{
            "source_id": "s1",
            "linked_hypotheses": [hid],
            "url_or_doi": "https://example.org/s1",
            "section": "results",
            "span": "p3",
            "claim": "x",
            "evidence_type": "case_study",
            "supports_or_challenges": "supports",
        }],
    )
    run_phase7(rs_blocked)
    rs_blocked.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]["validation_status"][
        "factual_consistency"
    ] = "disputed"
    run_phase8(rs_blocked)
    assert rs_blocked.promoted["phase8_finalizer"]["finalization"]["outcome"] == "blocked_finalization_report"
