#!/usr/bin/env python3
"""Visible WSL console for the 0714 AI research supervisor.

This process is a local user interface only. It does not SSH to the hospital,
change hospital services, install software, download databases, or mutate
analysis data. Hospital state is read from origin/main status files. The local
DeepSeek/Codex supervisor is invoked through the existing ai-supervisor CLI.

Interactive commands (press Enter after the command):
  w  run one forced 0714 watcher cycle now
  d  open the existing Supervisor `steer` interaction
  s  refresh Supervisor status immediately
  f  fetch origin/main immediately
  h  show help
  q  quit this console only (hospital/systemd work is unaffected)
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import select
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ASK_RE = re.compile(r"\bASK_USER\b|ACTION REQUIRED|approval required|user decision", re.I)
PENDING_RE = re.compile(r"(?:^|\n)\s*(?:status|state)\s*[:=]\s*(?:pending|ask_user|waiting_user)\b", re.I)
ANSI_CLEAR = "\033[2J\033[H"


@dataclass
class CommandResult:
    rc: int
    out: str


def run(args: list[str], *, cwd: Path | None = None, timeout: int = 30) -> CommandResult:
    try:
        p = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
        return CommandResult(p.returncode, p.stdout or "")
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return CommandResult(124, str(output) + "\nTIMEOUT")
    except OSError as exc:
        return CommandResult(127, f"{type(exc).__name__}: {exc}")


def tail(text: str, n: int = 12) -> str:
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-n:]) if lines else ""


def compact(text: str, width: int = 118) -> str:
    line = " ".join(text.strip().split())
    if len(line) <= width:
        return line
    return line[: max(0, width - 3)] + "..."


def parse_key_values(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def is_pending_decision(text: str, path: str = "") -> bool:
    return bool(PENDING_RE.search(text) or ASK_RE.search(text) or Path(path).name.lower().startswith("ask_"))


def contains_ask_user(text: str) -> bool:
    return bool(ASK_RE.search(text))


def watcher_error_tail(
    rc: int | None,
    output: str,
    *,
    active: bool,
    ask_user: bool,
    n: int = 5,
) -> list[str]:
    """Return compact watcher diagnostics only for an unexplained non-zero exit."""
    if rc in (None, 0) or active or ask_user:
        return []
    lines = [
        compact(line, 136)
        for line in tail(output, n).splitlines()
        if line.strip()
    ]
    return lines or ["(watcher produced no output)"]


class GitRemoteReader:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.last_fetch_at = 0.0
        self.last_fetch = CommandResult(0, "not fetched yet")

    def fetch(self) -> CommandResult:
        self.last_fetch = run(["git", "fetch", "origin", "main", "--quiet"], cwd=self.repo, timeout=120)
        self.last_fetch_at = time.time()
        return self.last_fetch

    def show(self, path: str) -> str:
        result = run(["git", "show", f"origin/main:{path}"], cwd=self.repo, timeout=20)
        return result.out if result.rc == 0 else ""

    def list_paths(self, prefix: str) -> list[str]:
        result = run(
            ["git", "ls-tree", "-r", "--name-only", "origin/main", "--", prefix],
            cwd=self.repo,
            timeout=20,
        )
        if result.rc != 0:
            return []
        return [line.strip() for line in result.out.splitlines() if line.strip()]

    def head(self) -> str:
        result = run(["git", "rev-parse", "--short=10", "origin/main"], cwd=self.repo)
        return result.out.strip() if result.rc == 0 else "unknown"


class SupervisorConsole:
    def __init__(
        self,
        repo: Path,
        supervisor_dir: Path,
        refresh_seconds: int,
        fetch_seconds: int,
        watcher_minutes: int,
        auto_watcher: bool,
    ) -> None:
        self.repo = repo
        self.supervisor_dir = supervisor_dir
        self.refresh_seconds = refresh_seconds
        self.fetch_seconds = fetch_seconds
        self.watcher_seconds = watcher_minutes * 60
        self.auto_watcher = auto_watcher
        self.remote = GitRemoteReader(repo)
        self.control = supervisor_dir / "src" / "control.mjs"
        self.events: list[str] = []
        self.last_supervisor_status = "not checked"
        self.last_watcher_output = "not run in this console session"
        self.last_watcher_rc: int | None = None
        self.last_watcher_started = 0.0
        self.watcher_thread: threading.Thread | None = None
        self.watcher_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        self.stop = False
        self.force_status_refresh = True

    def event(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"{stamp}  {message}")
        self.events = self.events[-10:]

    def supervisor_status(self) -> str:
        if not self.control.is_file():
            return f"control missing: {self.control}"
        result = run(["node", str(self.control), "status"], cwd=self.supervisor_dir, timeout=30)
        return result.out.strip() or f"control status rc={result.rc}"

    def start_watcher(self, reason: str) -> None:
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.event("watcher already active; duplicate launch skipped")
            return
        if not self.supervisor_dir.is_dir():
            self.event(f"ai-supervisor directory missing: {self.supervisor_dir}")
            return

        self.last_watcher_started = time.time()
        self.event(f"DeepSeek watcher started ({reason})")

        def worker() -> None:
            result = run(
                ["npm", "run", "watch:0714", "--", "--production", "--force"],
                cwd=self.supervisor_dir,
                timeout=60 * 60,
            )
            self.watcher_queue.put((result.rc, result.out))

        self.watcher_thread = threading.Thread(target=worker, daemon=True)
        self.watcher_thread.start()

    def drain_watcher(self) -> None:
        while True:
            try:
                rc, out = self.watcher_queue.get_nowait()
            except queue.Empty:
                break
            self.last_watcher_rc = rc
            self.last_watcher_output = out.strip() or "(watcher produced no output)"
            if contains_ask_user(self.last_watcher_output):
                self.event("⚠ DeepSeek returned ASK_USER / ACTION REQUIRED")
            else:
                self.event(f"DeepSeek watcher finished rc={rc}")
            self.force_status_refresh = True

    def maybe_fetch(self, force: bool = False) -> None:
        if force or time.time() - self.remote.last_fetch_at >= self.fetch_seconds:
            result = self.remote.fetch()
            if result.rc == 0:
                self.event(f"origin/main refreshed ({self.remote.head()})")
            else:
                self.event(f"git fetch failed rc={result.rc}: {compact(result.out)}")

    def maybe_watcher(self) -> None:
        if not self.auto_watcher:
            return
        if self.watcher_thread and self.watcher_thread.is_alive():
            return
        if self.last_watcher_started == 0 or time.time() - self.last_watcher_started >= self.watcher_seconds:
            self.start_watcher("scheduled console cycle")

    def hospital_state(self) -> tuple[dict[str, Any], dict[str, str]]:
        summary_text = self.remote.show("reports_public/metagenome_functional_profile/summary.json")
        runner_text = self.remote.show("reports_public/metagenome_functional_profile/runner_status.txt")
        try:
            summary = json.loads(summary_text) if summary_text else {}
        except json.JSONDecodeError:
            summary = {"state": "invalid summary.json"}
        return summary, parse_key_values(runner_text)

    def decisions(self) -> list[tuple[str, bool, str]]:
        rows: list[tuple[str, bool, str]] = []
        for path in self.remote.list_paths("decision_requests"):
            if path.endswith("/.gitkeep") or Path(path).name == ".gitkeep":
                continue
            text = self.remote.show(path)
            rows.append((path, is_pending_decision(text, path), compact(text, 145)))
        return rows

    def codex_state(self) -> str:
        result = run(["pgrep", "-af", "codex"], timeout=10)
        lines = [line for line in result.out.splitlines() if "research_supervisor_console" not in line]
        return tail("\n".join(lines), 4) if lines else "no local Codex process visible"

    def local_repo_state(self) -> str:
        branch = run(["git", "branch", "--show-current"], cwd=self.repo).out.strip() or "detached"
        head = run(["git", "rev-parse", "--short=10", "HEAD"], cwd=self.repo).out.strip() or "unknown"
        status = run(["git", "status", "--porcelain"], cwd=self.repo).out.strip()
        dirty = "dirty" if status else "clean"
        return f"{branch}@{head} ({dirty})"

    def render(self) -> None:
        summary, runner = self.hospital_state()
        decisions = self.decisions()
        pending = [row for row in decisions if row[1]]
        watcher_active = bool(self.watcher_thread and self.watcher_thread.is_alive())

        if self.force_status_refresh:
            self.last_supervisor_status = self.supervisor_status()
            self.force_status_refresh = False

        generated = summary.get("generated_at", runner.get("generated_at", "unknown"))
        state = summary.get("state", runner.get("state", "unknown"))
        reason = summary.get("reason", runner.get("reason", ""))
        done = summary.get("done_count", "?")
        running = summary.get("running_count", "?")
        failed = summary.get("failed_count", "?")
        queued = summary.get("queued_count", summary.get("skipped_count", "?"))
        route = summary.get("route", runner.get("route", "unknown"))

        ask_from_watcher = contains_ask_user(self.last_watcher_output)
        action_required = bool(pending or ask_from_watcher)

        lines = [
            "╔════════════════════ AI RESEARCH SUPERVISOR · 0714 ════════════════════╗",
            f"  Local time: {datetime.now().isoformat(timespec='seconds')}    origin/main: {self.remote.head()}",
            f"  Local repo: {self.local_repo_state()}",
            "",
            "[ HOSPITAL / HUMAnN ]",
            f"  state={state}  route={route}",
            f"  progress: done={done}  running={running}  failed={failed}  queued={queued}",
            f"  status timestamp: {generated}",
            f"  reason: {compact(str(reason), 132)}",
            "",
            "[ DEEPSEEK SUPERVISOR ]",
            f"  watcher: {'RUNNING' if watcher_active else 'idle'}  last_rc={self.last_watcher_rc if self.last_watcher_rc is not None else 'n/a'}",
            "  " + compact(self.last_supervisor_status, 140),
        ]

        watcher_error = watcher_error_tail(
            self.last_watcher_rc,
            self.last_watcher_output,
            active=watcher_active,
            ask_user=ask_from_watcher,
        )
        if watcher_error:
            lines.append("  ⚠ watcher ended non-zero; last output:")
            for line in watcher_error:
                lines.append("    " + line)

        lines += ["", "[ CODEX / LOCAL EXECUTOR ]"]
        for line in (self.codex_state().splitlines() or ["unknown"]):
            lines.append("  " + compact(line, 140))

        lines += ["", "[ DECISIONS ]"]
        if action_required:
            lines.append("  ⚠ ACTION REQUIRED")
            if ask_from_watcher:
                lines.append("  DeepSeek watcher output contains ASK_USER. Last lines:")
                for line in tail(self.last_watcher_output, 8).splitlines():
                    lines.append("    " + compact(line, 136))
            for path, _, preview in pending[-3:]:
                lines.append(f"  pending: {path}")
                lines.append("    " + preview)
            lines.append("  Type: d <Enter>  to open the existing Supervisor steer interaction.")
        else:
            lines.append("  no pending ASK_USER request detected")
            legacy = [row for row in decisions if not row[1]]
            if legacy:
                lines.append(f"  informational/legacy decision files: {len(legacy)}")

        lines += ["", "[ RECENT CONSOLE EVENTS ]"]
        lines.extend("  " + event for event in (self.events[-6:] or ["no events yet"]))
        lines += [
            "",
            "Commands: w=watch now   d=respond/steer   s=status   f=fetch   h=help   q=quit console",
            "Hospital systemd work continues even if this console is closed.",
            "╚═══════════════════════════════════════════════════════════════════════╝",
            "> ",
        ]
        sys.stdout.write(ANSI_CLEAR + "\n".join(lines))
        sys.stdout.flush()

    def steer(self) -> None:
        if not self.control.is_file():
            self.event(f"cannot steer; missing {self.control}")
            return
        sys.stdout.write("\nOpening existing Supervisor steer command. Follow its prompt; Ctrl+C returns here.\n")
        sys.stdout.flush()
        try:
            subprocess.run(["node", str(self.control), "steer"], cwd=str(self.supervisor_dir), check=False)
        except KeyboardInterrupt:
            pass
        self.event("Supervisor steer interaction returned")
        self.force_status_refresh = True

    def help(self) -> None:
        sys.stdout.write(
            "\n\nConsole commands:\n"
            "  w  force one DeepSeek/Codex 0714 watcher cycle\n"
            "  d  open ai-supervisor control.mjs steer (interactive decision response)\n"
            "  s  refresh ai-supervisor status\n"
            "  f  fetch origin/main now\n"
            "  q  close only this UI; hospital systemd jobs are not stopped\n"
            "Press Enter to return.\n"
        )
        sys.stdout.flush()
        try:
            input()
        except EOFError:
            pass

    def handle_command(self, command: str) -> None:
        cmd = command.strip().lower()
        if not cmd:
            return
        if cmd == "q":
            self.stop = True
        elif cmd == "w":
            self.start_watcher("manual command")
        elif cmd == "d":
            self.steer()
        elif cmd == "s":
            self.force_status_refresh = True
            self.event("Supervisor status refresh requested")
        elif cmd == "f":
            self.maybe_fetch(force=True)
        elif cmd == "h":
            self.help()
        else:
            self.event(f"unknown console command: {cmd}")

    def loop(self) -> int:
        self.maybe_fetch(force=True)
        self.force_status_refresh = True
        if self.auto_watcher:
            self.start_watcher("console startup")

        while not self.stop:
            self.drain_watcher()
            self.maybe_fetch()
            self.maybe_watcher()
            self.render()

            deadline = time.time() + self.refresh_seconds
            while time.time() < deadline and not self.stop:
                timeout = min(0.5, max(0.0, deadline - time.time()))
                try:
                    ready, _, _ = select.select([sys.stdin], [], [], timeout)
                except (OSError, ValueError):
                    time.sleep(timeout)
                    continue
                if ready:
                    line = sys.stdin.readline()
                    if line == "":
                        self.stop = True
                        break
                    self.handle_command(line)
                    break
                self.drain_watcher()
        sys.stdout.write("\nSupervisor console closed. No hospital job was stopped.\n")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.home() / "projects" / "0714")
    parser.add_argument("--supervisor-dir", type=Path, default=Path.home() / "ai-supervisor")
    parser.add_argument("--refresh-seconds", type=int, default=10)
    parser.add_argument("--fetch-seconds", type=int, default=60)
    parser.add_argument("--watcher-minutes", type=int, default=60)
    parser.add_argument(
        "--auto-watcher",
        action="store_true",
        help="run the existing DeepSeek 0714 watcher at console startup and then at the configured interval",
    )
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    supervisor_dir = args.supervisor_dir.expanduser().resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: 0714 git repository not found: {repo}", file=sys.stderr)
        return 2
    if args.refresh_seconds < 2 or args.fetch_seconds < 10 or args.watcher_minutes < 10:
        print("ERROR: unsafe/overly aggressive polling interval", file=sys.stderr)
        return 2

    console = SupervisorConsole(
        repo=repo,
        supervisor_dir=supervisor_dir,
        refresh_seconds=args.refresh_seconds,
        fetch_seconds=args.fetch_seconds,
        watcher_minutes=args.watcher_minutes,
        auto_watcher=args.auto_watcher,
    )
    return console.loop()


if __name__ == "__main__":
    raise SystemExit(main())
