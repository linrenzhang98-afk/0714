# ETYY reviewed queue

Each JSON envelope must contain `schema_version`, `job_id`, `authorized: true`,
`authorization_record`, `execution_commit`, `job_definition_path`,
`job_definition_sha256`, transfer/resource caps, allowed source hosts/roots, and a
handoff allowlist. The agent fetches and detaches exactly `execution_commit`; it never
executes moving `main`. ETYY writes only bounded metadata to `etty-handoff`.
