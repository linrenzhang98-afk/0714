#!/usr/bin/env python3
"""Domain-agnostic bounded acquisition and command-execution primitives."""
from __future__ import annotations

import errno
import hashlib
import http.client
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class JobError(Exception):
    pass


def atomic(path: Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confined(path: Path | str, roots: list[str]) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise JobError("path must be absolute without traversal")
    effective = candidate.resolve(strict=False)
    for raw_root in roots:
        root = Path(raw_root).resolve(strict=True)
        if effective == root or root in effective.parents:
            if candidate.is_symlink() and candidate.resolve(strict=False) != effective:
                raise JobError("symlink escape")
            return candidate
    raise JobError("path escapes allowed roots")


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("authorized") is not True:
        raise JobError("manifest is not explicitly authorized")
    items = manifest.get("items")
    roots = manifest.get("allowed_destination_roots")
    hosts = manifest.get("allowed_hosts", manifest.get("allowed_source_hosts"))
    cap = manifest.get("transfer_cap_bytes")
    if not isinstance(items, list) or not items or not isinstance(roots, list) or not roots:
        raise JobError("manifest items/destination roots are invalid")
    if not isinstance(hosts, list) or not hosts or not isinstance(cap, int) or cap <= 0:
        raise JobError("manifest hosts/transfer cap are invalid")
    ids: set[str] = set()
    destinations: set[str] = set()
    expected_total = 0
    allowed_schemes = {"https"}
    if os.environ.get("ETTY_SYNTHETIC_HTTP") == "1":
        allowed_schemes.add("http")
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in ids:
            raise JobError("duplicate or invalid item id")
        ids.add(item_id)
        parsed = urllib.parse.urlparse(item.get("url", ""))
        if parsed.scheme not in allowed_schemes or parsed.hostname not in hosts:
            raise JobError("source URL is outside the allowlist")
        destination = confined(item.get("destination", ""), roots)
        effective_destination = str(destination.resolve(strict=False))
        if effective_destination in destinations:
            raise JobError("duplicate destination")
        destinations.add(effective_destination)
        expected = item.get("expected_bytes")
        if not isinstance(expected, int) or expected <= 0:
            raise JobError("expected_bytes must be positive")
        expected_total += expected
    if expected_total > cap:
        raise JobError("expected transfer exceeds cap")
    return items


def _bounded_error_detail(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:300]


def _is_transient_network_error(exc: BaseException) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return 500 <= exc.code <= 599
    if isinstance(exc, (urllib.error.URLError, http.client.HTTPException)):
        return True
    if isinstance(exc, (TimeoutError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError, ConnectionRefusedError)):
        return True
    return isinstance(exc, OSError) and exc.errno in {
        errno.ENETDOWN,
        errno.ENETUNREACH,
        errno.ENETRESET,
        errno.ECONNABORTED,
        errno.ECONNRESET,
        errno.ECONNREFUSED,
        errno.ETIMEDOUT,
        errno.EHOSTUNREACH,
        errno.EPIPE,
    }


def acquire(
    manifest: dict[str, Any],
    state_path: Path,
    retries_per_pass: int = 2,
    retry_passes: int = 2,
    backoff_seconds: tuple[float, ...] = (1.0, 2.0),
    sleep_fn=time.sleep,
) -> dict[str, Any]:
    """Acquire every item with fail-soft transient isolation and a fail-closed final gate.

    Integrity and policy errors stop immediately. Transient network failures are
    durable per item, do not prevent later items from running, and receive bounded
    later passes. The total attempt ceiling survives process restarts.
    """
    items = validate_manifest(manifest)
    if retries_per_pass < 1 or retry_passes < 0:
        raise JobError("retry policy is invalid")
    state_path = Path(state_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "network_bytes": 0,
        "items": {},
    }
    if not isinstance(state.get("network_bytes"), int) or state["network_bytes"] < 0:
        raise JobError("acquisition state network byte counter is invalid")
    if not isinstance(state.get("items"), dict):
        raise JobError("acquisition item state is invalid")
    cap = manifest["transfer_cap_bytes"]
    if state["network_bytes"] > cap:
        raise JobError("persisted cumulative transfer exceeds cap")
    allowed_hosts = manifest.get("allowed_hosts") or manifest.get("allowed_source_hosts", [])
    max_total_attempts = retries_per_pass * (retry_passes + 1)
    item_by_id = {item["id"]: item for item in items}

    def mark_existing(item: dict[str, Any]) -> bool:
        destination = confined(item["destination"], manifest["allowed_destination_roots"])
        if not (destination.exists() or destination.is_symlink()):
            return False
        confined(destination, manifest["allowed_destination_roots"])
        if not destination.is_file() or destination.stat().st_size != item["expected_bytes"]:
            raise JobError(f"conflicting existing file: {item['id']}")
        actual_sha = sha256(destination)
        if item.get("sha256") and actual_sha != item["sha256"]:
            raise JobError(f"conflicting existing checksum: {item['id']}")
        previous = state["items"].get(item["id"], {})
        state["items"][item["id"]] = {
            **previous,
            "id": item["id"],
            "status": "reused" if previous.get("status") != "done" else "done",
            "actual_bytes": destination.stat().st_size,
            "sha256": actual_sha,
            "attempts": int(previous.get("attempts", 0)),
        }
        atomic(state_path, state)
        return True

    def attempt_item(item: dict[str, Any], pass_index: int) -> bool:
        if mark_existing(item):
            return True
        destination = confined(item["destination"], manifest["allowed_destination_roots"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        part = destination.with_name(destination.name + ".part")
        previous = state["items"].get(item["id"], {})
        attempts = int(previous.get("attempts", 0))
        if attempts >= max_total_attempts:
            state["items"][item["id"]] = {
                **previous,
                "id": item["id"],
                "status": "transient_failed",
                "attempts": attempts,
            }
            atomic(state_path, state)
            return False
        attempts_this_pass = min(retries_per_pass, max_total_attempts - attempts)
        for _ in range(attempts_this_pass):
            attempts += 1
            state["current_item"] = item["id"]
            state["items"][item["id"]] = {
                **state["items"].get(item["id"], {}),
                "id": item["id"],
                "status": "downloading",
                "attempts": attempts,
                "retry_pass": pass_index,
            }
            atomic(state_path, state)
            try:
                request = urllib.request.Request(item["url"])
                with urllib.request.urlopen(request, timeout=30) as response:
                    final_host = urllib.parse.urlparse(response.geturl()).hostname
                    if final_host not in allowed_hosts:
                        raise JobError("redirect host is outside the allowlist")
                    count = 0
                    digest = hashlib.sha256()
                    with part.open("wb") as output:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            projected = state["network_bytes"] + len(chunk)
                            if projected > cap:
                                atomic(state_path, state)
                                raise JobError("cumulative transfer cap exceeded")
                            output.write(chunk)
                            digest.update(chunk)
                            count += len(chunk)
                            state["network_bytes"] = projected
                            state["items"][item["id"]]["network_bytes_this_attempt"] = count
                            atomic(state_path, state)
                        output.flush()
                        os.fsync(output.fileno())
                if count != item["expected_bytes"]:
                    raise JobError(f"downloaded byte count mismatch: {item['id']}")
                actual_sha = digest.hexdigest()
                if item.get("sha256") and actual_sha != item["sha256"]:
                    raise JobError(f"downloaded checksum mismatch: {item['id']}")
                part.replace(destination)
                state["items"][item["id"]] = {
                    **state["items"].get(item["id"], {}),
                    "id": item["id"],
                    "status": "done",
                    "actual_bytes": count,
                    "sha256": actual_sha,
                    "attempts": attempts,
                }
                atomic(state_path, state)
                return True
            except JobError:
                raise
            except Exception as exc:
                if not _is_transient_network_error(exc):
                    raise JobError(
                        f"non-transient acquisition error: {type(exc).__name__}: {_bounded_error_detail(exc)}"
                    ) from exc
                state["items"][item["id"]].update({
                    "status": "retry_pending",
                    "last_error_type": type(exc).__name__,
                    "last_error_detail": _bounded_error_detail(exc),
                })
                atomic(state_path, state)
        state["items"][item["id"]]["status"] = (
            "transient_failed" if attempts >= max_total_attempts else "retry_pending"
        )
        atomic(state_path, state)
        return False

    pending = list(items)
    for pass_index in range(retry_passes + 1):
        if pass_index and pending and all(
            int(state["items"].get(item["id"], {}).get("attempts", 0)) >= max_total_attempts
            for item in pending
        ):
            break
        if pass_index and pending:
            delay = backoff_seconds[min(pass_index - 1, len(backoff_seconds) - 1)] if backoff_seconds else 0
            if delay > 0:
                sleep_fn(delay)
        next_pending: list[dict[str, Any]] = []
        for item in pending:
            if not attempt_item(item, pass_index):
                next_pending.append(item)
        pending = next_pending
        completed = sum(
            state["items"].get(item_id, {}).get("status") in {"done", "reused"}
            for item_id in item_by_id
        )
        state.update({
            "status": "running" if pending else "done",
            "completed_items": completed,
            "total_items": len(items),
            "pending_retry_items": [item["id"] for item in pending],
            "current_item": None,
        })
        atomic(state_path, state)
        if not pending:
            return state

    failed_ids = sorted(item["id"] for item in pending)
    state.update({
        "status": "transient_failed",
        "failed_items": len(failed_ids),
        "failed_item_ids": failed_ids,
        "current_item": None,
    })
    atomic(state_path, state)
    raise JobError(
        f"unresolved transient acquisition failures ({len(failed_ids)}): {','.join(failed_ids[:20])}"
    )


def _command_identity(item: dict[str, Any], manifest: dict[str, Any]) -> str:
    material = {"command": item["command"], "cwd": item.get("cwd", manifest.get("cwd")), "env": item.get("env", {})}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def execute(manifest: dict[str, Any], state_path: Path) -> dict[str, Any]:
    items = validate_manifest(manifest)
    state_path = Path(state_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {"items": {}}
    allowed_executables = manifest.get("allowed_executables")
    working_roots = manifest.get("allowed_working_roots")
    environment_keys = set(manifest.get("allowed_environment_keys", []))
    if not isinstance(allowed_executables, list) or not allowed_executables:
        raise JobError("allowed_executables is required")
    if not isinstance(working_roots, list) or not working_roots:
        raise JobError("allowed_working_roots is required")
    exact_executable = manifest.get("executable_path")
    if exact_executable and exact_executable not in allowed_executables:
        raise JobError("executable_path is outside executable allowlist")
    if manifest.get("version_command") is not None:
        version_command = manifest["version_command"]
        if not isinstance(version_command, list) or not version_command or version_command[0] not in allowed_executables:
            raise JobError("version command is not allowed")
        probe = subprocess.run(version_command, shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        if probe.returncode or probe.stdout.strip() != manifest.get("version_expected"):
            raise JobError("executable version mismatch")
    for item in items:
        command = item.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(arg, str) for arg in command):
            raise JobError("command must be an argv string list")
        executable = command[0]
        if executable not in allowed_executables:
            raise JobError("executable is outside allowlist")
        if exact_executable and executable != exact_executable:
            raise JobError("executable path drift")
        cwd = confined(item.get("cwd", manifest.get("cwd", "")), working_roots)
        requested_environment = item.get("env", {})
        if not isinstance(requested_environment, dict) or not set(requested_environment).issubset(environment_keys):
            raise JobError("environment key is outside allowlist")
        identity = _command_identity(item, manifest)
        old = state["items"].get(item["id"])
        if old and old.get("command_hash") != identity:
            raise JobError("command identity changed")
        if old and old.get("status") == "done":
            continue
        started = time.time()
        state["items"][item["id"]] = {"id": item["id"], "command_hash": identity, "status": "running", "started_at": started}
        atomic(state_path, state)
        child_environment = {key: os.environ[key] for key in environment_keys if key in os.environ}
        child_environment.update(requested_environment)
        try:
            result = subprocess.run(
                command, cwd=cwd, env=child_environment, shell=False, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=int(manifest["wall_seconds"]),
            )
        except subprocess.TimeoutExpired as exc:
            state["items"][item["id"]].update({"status": "timeout", "finished_at": time.time()})
            atomic(state_path, state)
            raise JobError("command wall-time exceeded") from exc
        state["items"][item["id"]].update({
            "status": "done" if result.returncode == 0 else "failed", "returncode": result.returncode,
            "finished_at": time.time(), "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:],
        })
        atomic(state_path, state)
        if result.returncode != 0:
            raise JobError("command returned nonzero")
    return state
