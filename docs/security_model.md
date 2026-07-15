# Security Model

## What This Runner Allows

GitHub can submit structured jobs such as:

- `run_metabolomics_analysis`
- `generate_report`
- `backup_results`

Each job contains parameters, not shell commands.

## What This Runner Rejects

The runner does not execute:

- `cmd`
- `command`
- `shell`
- `bash`
- `powershell`
- arbitrary executable paths from job files

Only task names present in the local `config.json` allowlist can run.

## Trust Boundary

Trusted locally:

- `runner.py`
- `config.json`
- local allowlisted scripts
- Linux service account permissions

Untrusted or semi-trusted from GitHub:

- `jobs/*.json`
- job parameters

## Required Operating Rules

- Use a private GitHub repository.
- Use a dedicated Linux user such as `analysis-runner`.
- Do not run the service as `root`.
- Keep `config.json` local, or store it in a separate private admin repository.
- Restrict writable paths with systemd `ReadWritePaths`.
- Keep real raw data outside the GitHub repository.
- Allow only approved data roots in `allowed_data_roots`.
- Review scripts before adding them to the allowlist.

## Why Not Run Arbitrary Commands

Pulling commands from GitHub and running them directly is equivalent to remote code execution. If the repository, token, branch, or workflow is compromised, the workstation is compromised.

This project keeps GitHub as a job queue, not as a shell.

