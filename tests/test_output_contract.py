from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.output_contract import build_terminal_report
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.graph.phase8 import run_phase8
from doc3_executor.schemas.models import RunState


def _run_to_phase8():
    rs = RunState(run_id="run_oc", trace_id="trace_oc")
    run_phase1(rs, "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники")
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
    run_phase8(rs)
    return rs


def test_oc_exactly_one_report():
    rs = _run_to_phase8()
    out = build_terminal_report(rs)
    assert "report_markdown" in out
    assert "terminal_error_return" not in out


def test_oc_report_envelope_present():
    rs = _run_to_phase8()
    out = build_terminal_report(rs)
    assert out["report_envelope"]["run_id"] == rs.run_id


def test_oc_markdown_envelope_consistency():
    rs = _run_to_phase8()
    out = build_terminal_report(rs)
    md = out["report_markdown"]
    assert f"run_id: {out['report_envelope']['run_id']}" in md
    assert f"report_type: {out['report_envelope']['report_type']}" in md


def test_oc_phase8_mapping_consistency():
    rs = _run_to_phase8()
    out = build_terminal_report(rs)
    outcome = rs.promoted["phase8_finalizer"]["finalization"]["outcome"]
    if outcome == "limited_synthesis":
        assert out["report_filename"] == "limited_synthesis_report.md"


def test_oc_blocked_report_no_synthesis():
    rs = _run_to_phase8()
    rs.promoted["phase7_verification_memory"]["verification_ledger"]["claim_records"][0]["validation_status"][
        "factual_consistency"
    ] = "disputed"
    run_phase8(rs)
    out = build_terminal_report(rs)
    assert out["report_type"] == "blocked"
    assert "No synthesis was produced because finalization is blocked." in out["report_markdown"]


def test_oc_protocol_error_no_false_report():
    rs = RunState(run_id="run_oc_err", trace_id="trace_oc_err")
    out = build_terminal_report(rs)
    assert "terminal_error_return" in out
    assert "report_markdown" not in out

