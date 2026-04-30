from __future__ import annotations

import argparse

from doc3_executor.graph.output_contract import deliver_report
from doc3_executor.runner import run_workflow_resilient


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Doc3 resilient workflow (Phase 1->8).")
    parser.add_argument("--input", required=True, help="User plain-language request")
    parser.add_argument("--run-id", default="run_cli")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--base-dir", default="runs")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    payload = run_workflow_resilient(args.input, run_id=args.run_id, max_attempts=args.max_attempts)
    payload = deliver_report(payload, base_dir=args.base_dir, write_to_file=args.write_report, print_to_stdout=args.stdout)

    if "terminal_error_return" in payload:
        print(payload["terminal_error_return"])
    else:
        print(
            {
                "report_type": payload["report_type"],
                "report_filename": payload["report_filename"],
                "artifact_path": payload.get("artifact_path"),
            }
        )


if __name__ == "__main__":
    main()

