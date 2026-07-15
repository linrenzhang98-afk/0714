#!/usr/bin/env python3
"""Safe GitHub-controlled analysis runner.

This program pulls a Git repository on a schedule, reads structured JSON jobs,
and executes only locally configured allowlisted tasks. It never executes shell
commands supplied by GitHub job files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_JOB_KEYS = {"job_id", "task", "created_at", "params"}
FINAL_STATES = {"done", "failed", "rejected"}


class RunnerError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RunnerError(f"Expected JSON object in {path}")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": utc_now(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_under(base: Path, candidate: Path) -> Path:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved != base_resolved and base_resolved not in candidate_resolved.parents:
        raise RunnerError(f"Path escapes allowed base: {candidate}")
    return candidate_resolved


def run_checked(args: list[str], cwd: Path | None, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def git_pull(repo_path: Path, timeout: int, log_path: Path) -> None:
    result = run_checked(["git", "-C", str(repo_path), "pull", "--ff-only"], None, timeout)
    append_jsonl(
        log_path,
        {
            "event": "git_pull",
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        },
    )
    if result.returncode != 0:
        raise RunnerError("git pull failed; see runner log")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"jobs": {}}
    state = load_json(path)
    if "jobs" not in state or not isinstance(state["jobs"], dict):
        raise RunnerError("State file is invalid: missing jobs object")
    return state


def validate_config(config: dict[str, Any]) -> None:
    required = [
        "repo_path",
        "jobs_glob",
        "state_path",
        "log_path",
        "results_root",
        "allowed_data_roots",
        "tasks",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise RunnerError(f"Config missing required keys: {', '.join(missing)}")
    if not isinstance(config["tasks"], dict) or not config["tasks"]:
        raise RunnerError("Config tasks must be a non-empty object")
    if not isinstance(config["allowed_data_roots"], list) or not config["allowed_data_roots"]:
        raise RunnerError("Config allowed_data_roots must be a non-empty list")


def validate_job(job: dict[str, Any], allowed_tasks: set[str]) -> None:
    missing = REQUIRED_JOB_KEYS - set(job)
    if missing:
        raise RunnerError(f"Job missing required keys: {', '.join(sorted(missing))}")
    if not isinstance(job["job_id"], str) or not job["job_id"].strip():
        raise RunnerError("job_id must be a non-empty string")
    if not isinstance(job["task"], str) or job["task"] not in allowed_tasks:
        raise RunnerError(f"Task is not allowlisted: {job.get('task')!r}")
    if not isinstance(job["params"], dict):
        raise RunnerError("params must be an object")


def validate_dataset_path(params: dict[str, Any], allowed_roots: list[Path]) -> None:
    dataset_path = params.get("dataset_path")
    if dataset_path is None:
        return
    if not isinstance(dataset_path, str) or not dataset_path:
        raise RunnerError("params.dataset_path must be a non-empty string")
    candidate = Path(dataset_path).expanduser()
    if not candidate.is_absolute():
        raise RunnerError("params.dataset_path must be absolute")
    for root in allowed_roots:
        try:
            resolve_under(root, candidate)
            return
        except RunnerError:
            pass
    raise RunnerError("params.dataset_path is outside allowed_data_roots")


def execute_job(
    job_path: Path,
    job: dict[str, Any],
    config: dict[str, Any],
    state: dict[str, Any],
    dry_run: bool,
) -> None:
    job_id = job["job_id"]
    task_name = job["task"]
    task = config["tasks"][task_name]
    log_path = Path(config["log_path"]).expanduser()
    results_root = Path(config["results_root"]).expanduser()
    job_result_dir = results_root / job_id
    job_result_dir.mkdir(parents=True, exist_ok=True)

    script = Path(task["script"]).expanduser()
    if not script.is_absolute():
        raise RunnerError(f"Task script must be absolute: {script}")
    if not script.exists():
        raise RunnerError(f"Task script does not exist: {script}")

    timeout = int(task.get("timeout_seconds", config.get("default_task_timeout_seconds", 3600)))
    args = [sys.executable, str(script), "--job", str(job_path), "--out", str(job_result_dir)]

    append_jsonl(
        log_path,
        {
            "event": "job_start",
            "job_id": job_id,
            "task": task_name,
            "job_path": str(job_path),
            "job_sha256": sha256_file(job_path),
            "dry_run": dry_run,
        },
    )

    if dry_run:
        state["jobs"][job_id] = {
            "status": "done",
            "task": task_name,
            "dry_run": True,
            "updated_at": utc_now(),
            "job_path": str(job_path),
        }
        append_jsonl(log_path, {"event": "job_dry_run_ok", "job_id": job_id, "would_run": args})
        return

    start = time.time()
    result = run_checked(args, cwd=script.parent, timeout=timeout)
    elapsed = round(time.time() - start, 3)
    status = "done" if result.returncode == 0 else "failed"
    state["jobs"][job_id] = {
        "status": status,
        "task": task_name,
        "returncode": result.returncode,
        "elapsed_seconds": elapsed,
        "updated_at": utc_now(),
        "job_path": str(job_path),
        "result_dir": str(job_result_dir),
    }
    append_jsonl(
        log_path,
        {
            "event": "job_finish",
            "job_id": job_id,
            "task": task_name,
            "status": status,
            "returncode": result.returncode,
            "elapsed_seconds": elapsed,
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
        },
    )


def acquire_lock(lock_path: Path) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(lock_path), flags)
    except FileExistsError as exc:
        raise RunnerError(f"Another runner appears active: {lock_path}") from exc
    os.write(fd, str(os.getpid()).encode("ascii"))
    return fd


def release_lock(lock_path: Path, fd: int) -> None:
    os.close(fd)
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe GitHub-controlled analysis runner")
    parser.add_argument("--config", required=True, help="Path to local config JSON")
    parser.add_argument("--no-pull", action="store_true", help="Do not git pull before scanning jobs")
    parser.add_argument("--dry-run", action="store_true", help="Validate jobs without running task scripts")
    args = parser.parse_args()

    config = load_json(Path(args.config).expanduser())
    validate_config(config)

    repo_path = Path(config["repo_path"]).expanduser()
    log_path = Path(config["log_path"]).expanduser()
    state_path = Path(config["state_path"]).expanduser()
    lock_path = Path(config.get("lock_path", str(state_path) + ".lock")).expanduser()
    allowed_roots = [Path(p).expanduser().resolve() for p in config["allowed_data_roots"]]

    fd = acquire_lock(lock_path)
    try:
        if not args.no_pull:
            git_pull(repo_path, int(config.get("git_timeout_seconds", 120)), log_path)

        state = load_state(state_path)
        job_paths = sorted(repo_path.glob(config["jobs_glob"]))
        append_jsonl(log_path, {"event": "scan", "job_count": len(job_paths), "dry_run": args.dry_run})

        for job_path in job_paths:
            try:
                job = load_json(job_path)
                validate_job(job, set(config["tasks"]))
                validate_dataset_path(job["params"], allowed_roots)
                existing = state["jobs"].get(job["job_id"])
                if existing and existing.get("status") in FINAL_STATES:
                    continue
                execute_job(job_path, job, config, state, args.dry_run)
            except Exception as exc:  # noqa: BLE001 - log and continue with other jobs
                job_id = "unknown"
                try:
                    raw_job = load_json(job_path)
                    job_id = str(raw_job.get("job_id", "unknown"))
                except Exception:
                    pass
                state["jobs"][job_id] = {
                    "status": "rejected",
                    "updated_at": utc_now(),
                    "job_path": str(job_path),
                    "error": str(exc),
                }
                append_jsonl(log_path, {"event": "job_rejected", "job_id": job_id, "error": str(exc)})

        save_json(state_path, state)
        return 0
    except Exception as exc:
        append_jsonl(log_path, {"event": "runner_error", "error": str(exc)})
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        release_lock(lock_path, fd)


if __name__ == "__main__":
    raise SystemExit(main())
