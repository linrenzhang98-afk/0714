# Future workstation live visibility design

The existing ETYY backend remains authoritative. A separate persistent tmux session named `0714-live` may observe reviewed-job state and render current job ID, project/cohort, stage, completed/total items, elapsed time, latest event and warning/error, CPU, memory, load average, project disk usage, free disk, recent log lines, and queue state. The viewer is optional: closing it cannot stop a scientific job, and when no job runs it displays exactly `IDLE — waiting for reviewed job`. It must never fabricate activity or progress.

Future long jobs should expose `progress.json`, structured execution state, a line-buffered log (using tee where appropriate), and a human-readable live log. The observer reads these allowlisted artifacts; it does not become an execution dependency. This document proposes no current agent changes.
