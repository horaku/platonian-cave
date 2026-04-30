from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


REPORT_FILE_BY_OUTCOME = {
    "authoritative_synthesis": "authoritative_synthesis_report.md",
    "limited_synthesis": "limited_synthesis_report.md",
    "blocked_finalization_report": "blocked_finalization_report.md",
}
REPORT_TYPE_BY_OUTCOME = {
    "authoritative_synthesis": "authoritative",
    "limited_synthesis": "limited",
    "blocked_finalization_report": "blocked",
}


def _front_matter(envelope: Dict) -> str:
    lines = ["---"]
    for k in ["report_type", "run_id", "generated_at_utc", "protocol_version", "finalization_status"]:
        lines.append(f"{k}: {envelope[k]}")
    lines.append("based_on:")
    lines.append("  promoted_records:")
    for r in envelope["based_on"]["promoted_records"]:
        lines.append(f"    - {r}")
    lines.append("  decision_event_ids:")
    for e in envelope["based_on"]["decision_event_ids"]:
        lines.append(f"    - {e}")
    lines.append("---")
    return "\n".join(lines)


def build_terminal_report(run_state) -> Dict:
    p8 = run_state.promoted.get("phase8_finalizer")
    if not p8:
        return terminal_error_return(run_state, "missing promoted phase8_finalizer", safe_to_retry=True)

    finalization = p8.get("finalization", {})
    outcome = finalization.get("outcome")
    if outcome not in REPORT_FILE_BY_OUTCOME:
        return terminal_error_return(run_state, "invalid phase8 outcome", safe_to_retry=False)

    report_type = REPORT_TYPE_BY_OUTCOME[outcome]
    filename = REPORT_FILE_BY_OUTCOME[outcome]
    now = datetime.now(timezone.utc).isoformat()
    envelope = {
        "report_type": report_type,
        "run_id": run_state.run_id,
        "generated_at_utc": now,
        "protocol_version": "v0",
        "finalization_status": finalization.get("finalization_status", report_type),
        "based_on": {
            "promoted_records": list(run_state.promoted.keys()),
            "decision_event_ids": [e.record_id for e in run_state.events],
        },
    }

    if report_type == "blocked":
        main = "No synthesis was produced because finalization is blocked."
    else:
        main = finalization.get("report", {}).get("main_synthesis", "")

    md = "\n".join(
        [
            _front_matter(envelope),
            "# Doc3 Executor Report",
            "",
            "## 6.1 Main synthesis",
            main,
        ]
    )
    return {
        "report_markdown": md,
        "report_filename": filename,
        "report_type": report_type,
        "report_envelope": envelope,
    }


def terminal_error_return(run_state, reason: str, safe_to_retry: bool) -> Dict:
    diagnostic_event_id = run_state.events[-1].record_id if run_state.events else None
    return {
        "terminal_error_return": {
            "error_type": "terminal_error",
            "run_id": getattr(run_state, "run_id", None),
            "reason": reason,
            "diagnostic_event_id": diagnostic_event_id,
            "safe_to_retry": safe_to_retry,
        }
    }

