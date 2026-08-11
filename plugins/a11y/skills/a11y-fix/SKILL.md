---
name: a11y-fix
description: Apply approved fixes from an a11y-review accessibility report. Use when the user approves audit findings by ID ("/a11y-fix V1,V3", "apply all violations", "fix the contrast ones") after the a11y-review agent has produced a report.
---

# Apply approved accessibility fixes

You are applying findings the user has **already approved** from an `a11y-review` report. The audit's judgement calls were made; your job is to land them faithfully and catch anything that has drifted since.

## 1. Locate the report

In order of preference: the report in this conversation → `.a11y/report.md` → ask the user to run the `a11y-review` agent first. Do not reconstruct findings from scratch — if there is no report, stop and say so.

If the report exists only in conversation, write it to `.a11y/report.md` before editing anything. That file is the audit record and the idempotency baseline for the next run.

## 2. Resolve the selection

`$ARGUMENTS` names what to apply:

| Input | Means |
|---|---|
| `V1,V3,R2` | exactly those IDs |
| `all violations` / `all` | every 🔴 (never 🟡 or 🔵) |
| `all violations and risks` | 🔴 and 🟡 |
| a description ("the contrast ones") | matching findings — **echo the resolved ID list and confirm before editing** |
| empty | ask which findings to apply; list the IDs |

🔵 advisories and 🟡 risks are applied **only when named explicitly**. A risk was flagged because it needed confirmation the audit couldn't get — applying it silently defeats the purpose.

## 3. Check for drift

Before editing, re-hash every target file and compare against the report's `## Files audited` block:

```bash
shasum -a 256 <files> | cut -c1-12
```

If a hash differs, the file changed after the audit. Stop on that file, tell the user, and offer to re-audit it. Do not apply a diff to code you have not re-read — line numbers and surrounding context may have moved.

Then read each target file for real. The report shows fragments; you need the actual current context to edit safely.

## 4. Apply

- Make the **minimum** edit that resolves the finding. Nothing else — no reformatting, no import reordering, no drive-by refactors, no comments announcing the fix.
- Preserve design intent exactly as the report specified: lightness-only color moves, hit-area growth via padding or `::after` rather than resizing the visible control.
- Re-run the contrast script on any color you write, and paste the confirmed ratio — do not trust the report's number blindly:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/contrast.py" "#4c79b1" "#ffffff"
  ```
- When a fix converts a `div` to a native `<button>` or `<a>`, delete the keyboard handlers, `role`, and `tabIndex` that become redundant. Leaving them is a half-fix that can break the native behaviour.
- If a finding turns out to be wrong on inspection, or two approved fixes conflict, **skip it and report why**. Do not improvise a different fix the user did not approve.
- Never leave `// TODO: a11y` or placeholder comments.

## 5. Verify

After all edits:

- Run the project's typecheck / lint / build if one exists (`package.json` scripts). Report failures with the actual output — never claim a clean run you didn't see.
- Re-read each edited region and confirm layout, responsive behaviour, and application logic are untouched.
- Confirm no fix reintroduced another finding (a new focus style that fails contrast, a padding change that pushes a target under 24px).

## 6. Report

```markdown
**Applied {n} of {m} approved findings**

✅ V1 `src/Button.tsx:14` — #7a9cc6 → #4c79b1 (verified 4.50:1)
✅ V3 `src/Card.tsx:22` — div → <button>, removed 15 lines of key handling
⏭️ R2 `src/Nav.tsx:8` — skipped: file changed since audit, needs re-check

Checks: `npm run typecheck` passed · `npm run lint` passed
Still open: V5, A1 (not approved this round)
```

Then update `.a11y/report.md`: mark applied findings as resolved and refresh the `## Files audited` hashes to the new file contents, so the next `a11y-review` run correctly sees them as already handled.

State outcomes plainly. If something failed or was skipped, that is the most important line in the report — put it where it will be read.
