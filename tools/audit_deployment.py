"""Audit GitHub workflows and recent log files for deployment health."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


WorkflowSummary = Dict[str, List[str]]


def _read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def _parse_workflow(path: Path) -> Tuple[str, WorkflowSummary]:
    lines = _read_lines(path)
    name = path.stem
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip().strip('"') or name
            break

    jobs: WorkflowSummary = {}
    in_jobs = False
    current_job: str | None = None
    collecting_run = False
    run_indent = ""
    run_lines: List[str] = []

    job_header = re.compile(r"^ {2}([A-Za-z0-9_-]+):\s*$")
    run_header = re.compile(r"^(\s+)run:\s*(\|)?\s*(.*)$")

    for line in lines:
        if line.strip() == "jobs:":
            in_jobs = True
            current_job = None
            continue

        if not in_jobs:
            continue

        job_match = job_header.match(line)
        if job_match:
            if collecting_run and current_job:
                jobs[current_job].append("\n".join(run_lines).strip())
                collecting_run = False
                run_lines = []
            current_job = job_match.group(1)
            jobs.setdefault(current_job, [])
            continue

        if current_job is None:
            continue

        run_match = run_header.match(line)
        if run_match:
            if collecting_run:
                jobs[current_job].append("\n".join(run_lines).strip())
                run_lines = []
            indent, multiline, inline = run_match.groups()
            run_indent = indent
            if multiline:
                collecting_run = True
                if inline:
                    run_lines.append(inline)
            else:
                collecting_run = False
                jobs[current_job].append(inline.strip())
            continue

        if collecting_run:
            if line.startswith(f"{run_indent}  "):
                run_lines.append(line[len(run_indent) + 2 :])
                continue
            jobs[current_job].append("\n".join(run_lines).strip())
            collecting_run = False
            run_lines = []

    if collecting_run and current_job:
        jobs[current_job].append("\n".join(run_lines).strip())

    return name, jobs


def collect_workflows(directory: Path) -> Dict[str, WorkflowSummary]:
    summary: Dict[str, WorkflowSummary] = {}
    if not directory.exists():
        return summary
    for path in sorted(directory.glob("*.yml")):
        name, jobs = _parse_workflow(path)
        summary[name] = jobs
    for path in sorted(directory.glob("*.yaml")):
        name, jobs = _parse_workflow(path)
        summary[name] = jobs
    return summary


def evaluate_workflows(workflows: Dict[str, WorkflowSummary]) -> Dict[str, object]:
    checks = []
    combined_commands = [cmd for jobs in workflows.values() for commands in jobs.values() for cmd in commands if cmd]

    def add_check(description: str, predicate: bool) -> None:
        checks.append({"description": description, "passed": predicate})

    add_check("frontend build step present", any("npm run build" in cmd for cmd in combined_commands))
    add_check("frontend tests executed", any("npm run test" in cmd for cmd in combined_commands))
    add_check("frontend lint executed", any("npm run lint" in cmd for cmd in combined_commands))
    add_check(
        "backend unit tests executed",
        any("python -m unittest" in cmd or "pytest" in cmd for cmd in combined_commands),
    )

    overall = all(check["passed"] for check in checks)
    return {"checks": checks, "passed": overall}


def _tail(path: Path, max_lines: int = 20) -> List[str]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
    except OSError:
        return []
    return [line.rstrip("\n") for line in lines[-max_lines:]]


def collect_logs(paths: Iterable[Path]) -> Dict[str, List[str]]:
    results: Dict[str, List[str]] = {}
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            results[str(base)] = _tail(base)
            continue
        for log_path in sorted(base.rglob("*.log")):
            results[str(log_path)] = _tail(log_path)
    return results


def build_log_targets() -> List[Path]:
    home = Path(os.path.expanduser("~"))
    return [
        Path("logs"),
        Path("web/frontend/.next/logs"),
        Path("web/backend/logs"),
        Path(".vercel/output/logs"),
        home / ".npm" / "_logs",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit workflows and deployment logs")
    parser.add_argument(
        "--mode",
        choices=["all", "workflows", "logs"],
        default="all",
        help="Audit workflows, logs, or both.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with a non-zero status when required checks are missing.",
    )
    args = parser.parse_args()

    workflows_summary: Dict[str, WorkflowSummary] = {}
    workflow_report: Dict[str, object] | None = None
    if args.mode in {"all", "workflows"}:
        workflows_summary = collect_workflows(Path(".github/workflows"))
        workflow_report = evaluate_workflows(workflows_summary)

    log_report: Dict[str, List[str]] | None = None
    if args.mode in {"all", "logs"}:
        log_report = collect_logs(build_log_targets())

    output = {
        "workflows": workflows_summary,
        "workflow_checks": workflow_report,
        "logs": log_report,
    }

    print(json.dumps(output, indent=2, sort_keys=True))

    if args.check and workflow_report and not workflow_report.get("passed", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
