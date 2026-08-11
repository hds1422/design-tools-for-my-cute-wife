# design-tools

Claude Code plugins for design and front-end work.

## Plugins

### `a11y` — WCAG 2.2 AA accessibility review

A two-step audit built so the reviewer **cannot** silently rewrite your design. Two named agents:

- **Paul** — the auditor. Read-only, no write tools, so "never change my files without approval" is enforced by the tool list rather than by good behaviour. Returns a ranked report with `file:line` anchors and exact proposed diffs.
- **Ally** (`/ally`) — the fixer. Applies findings you approve by ID, re-verifies them, and reports what it skipped.
- **`scripts/contrast.py`** — real WCAG contrast math both agents rely on. It's run rather than eyeballed, and it suggests the nearest compliant shade with hue and saturation preserved, so a contrast fix never drifts into a different color.

## Install

```bash
/plugin marketplace add harshsmac/claude-design-tools
/plugin install a11y@design-tools
```

To install from a local clone instead of GitHub:

```bash
/plugin marketplace add ~/Projects/claude-design-tools
/plugin install a11y@design-tools
```

## Use

```
use Paul to audit src/components/Button.tsx
```

Review the report, then apply what you want:

```
/ally V1,V3
/ally all violations
```

Findings are graded 🔴 **Violation** (fails a cited success criterion), 🟡 **Risk** (likely fails, needs runtime or visual confirmation), 🔵 **Advisory** (best practice or AAA). Risks and advisories are never applied unless you name them explicitly.

## Requirements

Python 3 (macOS ships it). No third-party packages.

## Notes

Reports are written to `.a11y/report.md` in the project being audited, with sha256 hashes of the files reviewed. A later run compares those hashes and skips files that have not changed, instead of re-auditing clean code.

Consider adding `.a11y/` to your project `.gitignore` if you don't want audit reports committed.
