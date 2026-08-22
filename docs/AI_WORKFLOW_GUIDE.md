# 0714 AI Workflow Guide

## 1. Purpose

This document is the durable operating guide for AI-assisted work in repository `linrenzhang98-afk/0714`.

It exists so that a new ChatGPT/Codex session can recover the established workflow without reconstructing the architecture from conversation history.

This document defines:

- automation topology
- authority boundaries
- ETYY execution rules
- Git/GitHub ownership
- safety and bounded-autonomy rules
- queue and handoff conventions
- new-pipeline onboarding
- operator interaction preferences
- recovery procedure for future sessions

This document is governance documentation.

It is NOT the authoritative source for current runtime state.

For live state, verify GitHub `main`, `etty-handoff`, job envelopes, exact commits, and generated handoff artifacts.

Never infer current execution state solely from this document.

---

## 2. Core topology

The established unattended workflow is:

User
→ ChatGPT / Codex
→ GitHub `main`
→ ETYY persistent outbound polling agent
→ exact reviewed execution commit
→ preflight
→ bounded acquisition
→ validation
→ bounded execution
→ `etty-handoff`
→ GitHub
→ ChatGPT / Codex continues downstream work

There is no normal inbound WSL/Codex → ETYY SSH execution path.

ETYY initiates outbound GitHub access.

Routine work must not require the user to log into ETYY and paste commands.

The user is not the automation trigger.

GitHub queue state is the trigger.

---

## 3. Git ownership boundaries

### `main`

WSL/Codex is the normal and sole automation writer to `main`.

Rules:

- normal commits only
- no force push
- no history rewriting
- no raw biological data in Git
- no secrets in Git
- no ETYY writes to `main`

ChatGPT should normally inspect GitHub read-only and instruct Codex when a `main` mutation is required.

### `etty-handoff`

ETYY may write only small, non-sensitive result/provenance artifacts to:

`etty-handoff`

ETYY must never push to `main`.

Handoff publication must:

- use normal commits
- never force push
- preserve existing branch history
- fail closed on conflicting or partially existing handoff state

---

## 4. ETYY unattended infrastructure

Production ETYY identity:

- host: `ETYY`
- user: `suma`

Control root:

`/mnt/disk1/0714_control`

Important directories:

- bootstrap:
  `/mnt/disk1/0714_control/bootstrap`

- installed immutable agent runtime:
  `/mnt/disk1/0714_control/agent_runtime`

- moving queue checkout:
  `/mnt/disk1/0714_control/queue_repo`

- exact per-job execution checkout:
  `/mnt/disk1/0714_control/job_repo`

- handoff checkout:
  `/mnt/disk1/0714_control/handoff_repo`

- durable state:
  `/mnt/disk1/0714_control/state`

- logs:
  `/mnt/disk1/0714_control/logs`

The installed unattended-agent baseline as of 2026-08-22 is:

`de0d7239c64fcd2ed0f2dfcbdf9818de51b32628`

This is a historical baseline reference, not permission to assume it remains current forever.
Always verify the live reviewed commit before infrastructure changes.

---

## 5. Scheduler

ETYY uses a user-level systemd oneshot service plus timer.

Current intended timer behavior:

- `OnBootSec=2min`
- `OnUnitActiveSec=3min`
- `Persistent=true`

Login-independent operation requires:

`Linger=yes`

This was explicitly enabled for user `suma`.

The unattended smoke test succeeded after the SSH session was closed, proving the persistent timer could:

1. discover a GitHub queue job,
2. execute it without an active SSH login,
3. publish its result to `etty-handoff`.

Do not require interactive ETYY login for routine jobs.

---

## 6. Legacy repository rule

The legacy/data checkout:

`/mnt/disk1/db/kraken2/0714/.git`

is NOT the control-plane repository.

Do NOT casually:

- repair it
- reset it
- rebase it
- clean it
- force checkout it
- use it as queue state
- treat local modifications there as a reason to repair Git

Data paths and control paths must remain conceptually separate.

---

## 7. Queue contract

Queue envelopes live under:

`automation/etty_jobs/<job_id>.json`

A production envelope is expected to bind the job to an exact immutable definition.

Important fields include:

- `schema_version`
- `job_id`
- `authorized`
- `authorization_record`
- `execution_commit`
- `job_definition_path`
- `job_definition_sha256`
- `transfer_cap_bytes`
- `allowed_source_hosts`
- `allowed_destination_roots`
- `resource_caps`
- `handoff_allowlist`

The agent must:

- fetch queue state from GitHub
- checkout the exact `execution_commit`
- verify the job-definition SHA256
- enforce the envelope as an upper bound
- fail closed if the job expands beyond the reviewed envelope

Never use a moving branch head as the scientific execution identity.

---

## 8. Bounded execution principles

Production automation must be bounded and fail closed.

Where applicable, enforce:

- explicit authorization
- exact commit
- exact job-definition hash
- destination-root confinement
- source-host allowlist
- transfer byte cap
- executable allowlist
- optional exact executable path
- working-directory root allowlist
- environment-key allowlist
- tool/version checks where scientifically relevant
- wall-time limit
- memory/resource limit where supported
- durable state
- restart-safe accounting
- command identity
- no shell interpolation when argv execution is sufficient
- no silent scope expansion

A failed safety check should produce `SAFE_STOP`, not an improvised workaround.

---

## 9. Acquisition rules

For external data acquisition:

- freeze the cohort first
- freeze expected byte counts when available
- freeze source URLs
- freeze destination paths
- define a cumulative network cap
- reject unexpected redirects/hosts
- use durable byte accounting
- do not treat partial files as complete
- verify final byte count
- compute local SHA256 after acquisition when upstream SHA256 is unavailable
- do not place acquired raw data into Git

Acquisition and scientific execution should be separate logical states.

Scientific execution should begin only after the acquisition gate passes.

### Durable lesson from the 2026-08-22 acquisition incident

For multi-item acquisition, transient network errors must be isolated per item so later items can continue. The agent may use bounded later retry passes, must reuse already validated files, and must keep cumulative network-byte accounting across failed attempts, retries, and restarts. Scientific execution still requires every required item to pass the final acquisition gate. Integrity, authorization, path, host, checksum, and other security-policy failures remain immediate fail-closed conditions. A terminal `SAFE_STOP` should be externally observable through a small, non-sensitive handoff artifact.

---

## 10. Execution idempotency

A completed reviewed command should not be re-executed merely because the polling agent runs again.

The system should distinguish:

- queued
- acquisition
- execution
- completed
- safe-stopped

Same job ID with a changed reviewed envelope is not automatically equivalent to the original job.

When state conflicts are detected, stop instead of guessing.

---

## 11. Handoff rules

ETYY handoff artifacts must be small and non-sensitive.

Typical allowed artifacts:

- `result.json`
- summaries
- provenance JSON
- validation reports
- status text
- small TSV/CSV result summaries where explicitly reviewed

Do NOT push:

- FASTQ
- BAM
- raw sequencing files
- large intermediate data
- sensitive credentials
- secrets
- unrestricted workstation logs

The handoff branch is the normal mechanism for ChatGPT/Codex to learn that ETYY completed work.

---

## 12. Human approval doctrine

The desired operating mode is bounded autonomy.

Do NOT repeatedly ask the user for approval for routine actions that remain within an already reviewed and explicitly authorized envelope.

Human confirmation is normally required for material changes such as:

- sudo/admin changes
- destructive filesystem actions
- destructive Git operations
- force push/history rewriting
- secrets or credential changes
- security-policy changes
- new external publication
- materially larger download/storage/compute scope
- scientifically meaningful cohort/sample expansion
- changing the biological/scientific analysis scope
- irreversible external actions

Past approval for one exact scope does not automatically authorize an unrelated future scope.

Conversely, do not repeatedly ask for approval for the exact same frozen scope once it has already been explicitly authorized.

---

## 13. Operator interaction preferences

The workflow should minimize manual operator burden.

Preferred behavior:

- do not make the user repeatedly log into ETYY
- do not use the user as an SSH bridge
- avoid trial-and-error command sequences
- verify repository state before proposing repairs
- prefer one precise action over many speculative actions
- when interactive terminal work is genuinely required, give one command at a time
- do not repeatedly move acceptance criteria after they have already been satisfied
- do not redesign a working architecture without concrete evidence of failure
- distinguish current verified state from inference
- report `SAFE_STOP` causes precisely

For long-running jobs, status should normally be checked from GitHub/handoff rather than asking the user to inspect ETYY manually.

---

## 14. Source of truth hierarchy

When resuming work, use this order:

1. exact GitHub commit contents
2. queue envelope
3. immutable execution job definition
4. `etty-handoff` artifacts
5. durable ETYY state when genuinely necessary
6. this guide
7. conversational memory

Conversation summaries and AI memory are useful context but are not authoritative runtime evidence.

Never claim that a task is running, finished, or failed solely because a prior conversation said so.

Verify live evidence.

---

## 15. New analysis-type onboarding

The ETYY control plane is intended to be reusable across projects and analysis types.

Examples may include:

- shotgun metagenomics
- 16S/ITS amplicon analysis
- RNA-seq/transcriptomics
- WGS
- generic Python/R statistical analysis

The scheduler/control architecture should NOT be rebuilt for each analysis type.

Instead create a reviewed analysis-specific executor/template.

Recommended onboarding lifecycle:

### Stage 1 — static review

Freeze:

- sample manifest
- input locations
- references/databases
- software versions
- command contract
- resource limits
- expected outputs
- handoff allowlist

### Stage 2 — synthetic test

Use:

- no real biological data where possible
- minimal commands
- bounded fake/synthetic fixtures

Confirm the control plane itself works.

### Stage 3 — small real pilot

Run a scientifically representative but small subset.

Confirm:

- tool availability
- database identity
- runtime
- memory
- disk use
- output validity
- provenance

### Stage 4 — frozen production

Only after the pilot passes:

- freeze production manifest
- freeze production execution commit
- create production queue envelope
- execute unattended

Do not silently convert a pilot-only executor into a production executor if it contains hard-coded pilot allowlists.

---

## 16. Reusable future template concept

Long-term, analysis types may expose stable templates such as:

- `shotgun_metagenome_v1`
- `amplicon_v1`
- `rnaseq_v1`
- `generic_analysis_v1`

A project-specific job should then mainly specify reviewed parameters such as:

- sample manifest
- input root
- output root
- database/reference identity
- threads
- memory
- wall time
- exact execution commit

Template reuse is preferred to repeatedly redesigning infrastructure.

---

## 17. Codex command approvals

Codex local command approval is independent of ETYY authorization.

An ETYY job may be fully authorized while Codex still asks permission to execute local WSL commands.

Where appropriate, reduce unnecessary Codex prompts through narrowly scoped allow rules for routine commands.

Do NOT solve prompt fatigue by broadly disabling all safety checks.

Keep explicit approval for high-risk actions such as:

- sudo
- destructive deletion
- force push
- credential changes
- system-level security changes

Prefer simple commands over complex shell heredocs/chains when rule matching matters.

---

## 18. Current verified infrastructure milestone

Historical milestone on 2026-08-22:

The unattended smoke job:

`20260822T090405Z-etty-unattended-smoke`

was queued through GitHub.

After the user's SSH session was closed, ETYY autonomously executed the job and published:

`handoffs/20260822T090405Z-etty-unattended-smoke/result.json`

with:

`status = done`

The corresponding ETYY handoff commit was:

`fe342c6fa73e018ecf25869bc48e2b0319317ff7`

This demonstrated the end-to-end control path:

Codex
→ GitHub `main`
→ unattended ETYY
→ execution
→ GitHub `etty-handoff`

Do not interpret this historical milestone as proof that every future job completed.
Future jobs require their own handoff evidence.

---

## 19. Current project snapshot — PRJCA046985

This section is intentionally a dated snapshot and may become stale.

As of 2026-08-22, the authorized remaining acquisition job was:

`20260822T092634Z-prjca046985-122-acquisition`

Execution-definition commit:

`aa061f53e928ba0adbbac83df21ccdf92a9d5f04`

Queue commit:

`b028af06c1cbce2cb4db07e8bdf0f0130c4443b8`

Frozen remaining run count:

`122`

Frozen exact source bytes:

`2,069,812,955`

Hard cumulative network cap:

`2,173,303,603`

Canonical destination root:

`/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq`

This snapshot is informational only.

Before continuing PRJCA046985 work, inspect the current GitHub queue and `etty-handoff`.

Do not infer completion from this document.

---

## 20. Session recovery procedure

When a new ChatGPT/Codex session starts:

1. Read this file.
2. Inspect current GitHub `main`.
3. Inspect the relevant queue envelope.
4. Inspect `etty-handoff`.
5. Identify the exact current execution commit.
6. Determine whether the last job is:
   - queued,
   - completed,
   - safe-stopped,
   - or unknown.
7. Continue from evidence.
8. Do not ask the user to repeat known project topology unless genuinely necessary.
9. Do not repair unrelated repository state.
10. Preserve existing architecture unless there is concrete evidence that it failed.

---

## 21. Security and data hygiene

Never place secrets in:

- Git commits
- queue envelopes
- handoff files
- documentation

Do not include:

- SSH private keys
- passwords
- API tokens
- personal credentials

Do not publish raw or sensitive biological/clinical data through Git merely to make automation convenient.

Use Git as control plane and small-result/provenance transport, not as a raw-data transport.

---

## 22. Change control for this guide

Update this guide when:

- control topology changes
- Git ownership rules change
- ETYY filesystem layout changes
- scheduler architecture changes
- approval doctrine changes
- a reusable pipeline standard is formally adopted

Do not update the permanent rules merely because one individual project changes.

Project-specific changing state should remain clearly labeled as a dated snapshot or live artifact.

When permanent governance and a project snapshot disagree:

- verify live repository evidence,
- then deliberately update the stale section.
