# 0714 repository operating rules

Before asking the user for execution authorization:

1. Read `automation/standing_authorization.json`.
2. If working on PRJCA046985, also read `automation/project_authorizations/PRJCA046985.json`.
3. If the requested action is explicitly within an ACTIVE authorization, do not ask the user to approve it again.
4. Authorization is scope-bounded. A new approval is required only when one of the `fresh_approval_required_if` conditions is triggered.
5. A technical failure or `SAFE_STOP` does not by itself invalidate authorization. Technical diagnostics or recovery may proceed without reapproval if the frozen scientific scope is unchanged.
6. Never interpret authorization as permission to:
   - force push;
   - perform destructive Git operations;
   - commit raw biological data;
   - expose secrets;
   - access ETYY via WSL SSH;
   - modify the legacy ETYY checkout;
   - bypass platform or tool safety restrictions.
7. Git ownership:
   - WSL/Codex is the sole writer to `main`.
   - ETYY Job Agent writes only `etty-handoff`.
8. Prefer:
   - immutable execution commits;
   - separate queue commits;
   - exact SHA256 pinning;
   - zero-download reuse;
   - fail-closed integrity gates;
   - externally observable handoffs.
9. When blocked by missing runtime evidence, report `EVIDENCE_REQUIRED` rather than asking for execution authorization again.
10. Do not redesign an already accepted scientific method unless the user explicitly asks for a redesign.
