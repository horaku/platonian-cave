from pathlib import Path

from doc3_executor.graph.output_contract import deliver_report
from doc3_executor.runner import run_workflow_resilient


def test_p10_runner_happy_path():
    payload = run_workflow_resilient(
        "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники",
        run_id="p10_happy",
    )
    assert "report_markdown" in payload
    assert payload["report_type"] in {"authoritative", "limited", "blocked"}


def test_p10_runner_revise_recovery():
    payload = run_workflow_resilient("Хочу понять, почему люди бросают сложные онлайн-курсы", run_id="p10_revise", max_attempts=3)
    assert "report_markdown" in payload
    assert payload["report_type"] in {"limited", "blocked", "authoritative"}


def test_p10_runner_reject_handling():
    payload = run_workflow_resilient("", run_id="p10_reject", max_attempts=1)
    assert "terminal_error_return" in payload
    assert payload["terminal_error_return"]["safe_to_retry"] is False


def test_p10_packaging_pyproject_has_src_discovery():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' in text
    assert 'where = ["src"]' in text


def test_p10_cli_windows_flow_like(tmp_path: Path):
    payload = run_workflow_resilient(
        "Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники",
        run_id="p10_cli",
    )
    delivered = deliver_report(payload, base_dir=str(tmp_path), write_to_file=True, print_to_stdout=False)
    assert "artifact_path" in delivered
    assert Path(delivered["artifact_path"]).exists()

