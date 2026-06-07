# CLAUDE.md

## Communication

Be concise. Short answers, minimal preamble. No over-explaining.

## Landing changes on `main`

Direct `git push` to `main` is blocked by the environment's branch lock
(pushes are restricted to the session branch; attempts to push `main`
fail with HTTP 503). To land work on `main`:

1. Push to the session branch.
2. Open/update a PR into `main`.
3. Merge it via the GitHub API (`mcp__github__merge_pull_request`) — this
   path is not affected by the push lock.

Do this automatically without asking each time (standing authorization).

## Repo note

The GitHub repository was renamed `Lunar-Moon` → `Moon-Phases`. The GitHub
MCP tools are still scoped to the old name (`MorrisB--/Lunar-Moon`), so use
that for API calls. Public raw URL uses the new name:
`https://raw.githubusercontent.com/MorrisB--/Moon-Phases/main/moon-phases.ics`
