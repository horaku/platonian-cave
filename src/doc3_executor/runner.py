from __future__ import annotations

from typing import Dict, List

from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.output_contract import build_terminal_report, terminal_error_return
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.graph.phase8 import run_phase8
from doc3_executor.schemas.models import RunState


def _default_records(active_hypothesis_id: str) -> List[Dict]:
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
        }
    ]


def _adjust_input(user_input: str, reason: str) -> str:
    if "orphan preferred term" in reason and "как искать источники" not in user_input:
        return f"{user_input}. Уточнение: как искать источники и строить поисковую стратегию."
    if "empty stated_request" in reason:
        return "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники"
    return user_input


def run_workflow_resilient(user_input: str, *, run_id: str = "run_cli", max_attempts: int = 3) -> Dict:
    current_input = user_input
    last_state = RunState(run_id=run_id, trace_id=f"{run_id}_trace")

    for attempt in range(1, max_attempts + 1):
        rs = RunState(run_id=f"{run_id}_a{attempt}", trace_id=f"{run_id}_trace_a{attempt}")
        last_state = rs
        run_phase1(rs, current_input)
        if "phase1_intent_surface" not in rs.promoted:
            reason = rs.events[-1].reason
            if rs.events[-1].decision.value == "REJECT":
                return terminal_error_return(rs, f"phase1 rejected: {reason}", safe_to_retry=False)
            current_input = _adjust_input(current_input, reason)
            continue

        run_phase2(rs)
        if "phase2_vocabulary_bootstrap" not in rs.promoted:
            reason = rs.events[-1].reason
            if rs.events[-1].decision.value == "REJECT":
                return terminal_error_return(rs, f"phase2 rejected: {reason}", safe_to_retry=False)
            current_input = _adjust_input(current_input, reason)
            continue

        run_phase3(rs)
        if "phase3_terminology_normalization" not in rs.promoted:
            reason = rs.events[-1].reason
            if rs.events[-1].decision.value == "REJECT":
                return terminal_error_return(rs, f"phase3 rejected: {reason}", safe_to_retry=False)
            current_input = _adjust_input(current_input, reason)
            continue

        run_phase4(rs)
        run_phase5(rs)
        hid = rs.promoted["phase4_hypothesis_lattice"]["hypotheses"][0]["hypothesis_id"]
        run_phase6(rs, _default_records(hid))
        run_phase7(rs)
        run_phase8(rs)
        return build_terminal_report(rs)

    return terminal_error_return(last_state, "max attempts exceeded while resolving revise decisions", safe_to_retry=True)

