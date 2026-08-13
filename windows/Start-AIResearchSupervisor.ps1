$ErrorActionPreference = 'Stop'

$WslCheckCommand = "pgrep -f '[r]esearch_supervisor_console.py' >/dev/null 2>&1"

& wsl.exe -- bash -lc $WslCheckCommand
$CheckRc = $LASTEXITCODE

if ($CheckRc -eq 0) {
    Write-Host "AI Research Supervisor is already running; duplicate launch skipped."
    exit 0
}

if ($CheckRc -ne 1) {
    throw "Unable to check existing WSL Supervisor process. wsl.exe exit code: $CheckRc"
}

$WslCommand = "cd ~/projects/0714 && exec python3 scripts/research_supervisor_console.py --auto-watcher"

if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
    Start-Process -FilePath "wt.exe" -ArgumentList @(
        "-w", "-1",
        "new-tab",
        "--title", "AI Research Supervisor",
        "wsl.exe", "--",
        "bash", "-lc", $WslCommand
    )
}
else {
    Start-Process -FilePath "wsl.exe" -ArgumentList @(
        "--",
        "bash", "-lc", $WslCommand
    )
}
