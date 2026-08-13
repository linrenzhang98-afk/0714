$ErrorActionPreference = 'Stop'

$WslCommand = "cd ~/projects/0714 && python3 scripts/research_supervisor_console.py --auto-watcher"

if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
    Start-Process -FilePath "wt.exe" -ArgumentList @(
        "new-tab",
        "--title", "AI Research Supervisor",
        "wsl.exe", "--", "bash", "-lc", $WslCommand
    )
} else {
    Start-Process -FilePath "wsl.exe" -ArgumentList @("--", "bash", "-lc", $WslCommand)
}
