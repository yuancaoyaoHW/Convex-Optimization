# Hypothesis Annotations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public visitor annotations to the GitHub Pages translation site.

**Architecture:** Each public HTML page loads the hosted Hypothes.is client before `</body>`. The client handles visitor login, annotation storage, and public display without adding a backend to this static site.

**Tech Stack:** Static HTML, Hypothes.is embed script, PowerShell verification commands.

---

### Task 1: Add Hypothes.is Client To Public Pages

**Files:**
- Modify: `translation/preface.html`
- Modify: `translation/ch01-introduction.html`
- Modify: `translation/ch02-convex-sets.html`
- Modify: `translation/ch03-convex-functions.html`
- Modify: `translation/ch04-convex-problems.html`
- Modify: `translation/ch05-duality.html`
- Modify: `translation/ch06-approximation.html`
- Modify: `translation/ch07-statistical-estimation.html`
- Modify: `translation/ch08-geometric-problems.html`
- Modify: `translation/ch09-unconstrained.html`
- Modify: `translation/ch10-equality-constrained.html`
- Modify: `translation/ch11-interior-point.html`
- Modify: `translation/appendix-a.html`
- Modify: `translation/appendix-b.html`
- Modify: `translation/appendix-c.html`

- [ ] **Step 1: Write the failing verification**

Run:

```powershell
$pages = Get-ChildItem -LiteralPath 'translation' -Filter '*.html' |
  Where-Object { $_.Name -ne 'index.html' }
$missing = $pages | Where-Object {
  -not (Select-String -LiteralPath $_.FullName -Pattern 'https://hypothes.is/embed.js' -SimpleMatch -Quiet)
}
if ($missing) {
  $missing | ForEach-Object { $_.Name }
  exit 1
}
```

Expected: FAIL and print the public page names, because the embed script is not present yet.

- [ ] **Step 2: Add the Hypothes.is embed script**

Insert this line before the closing `</body>` in each public chapter/appendix/preface page:

```html
  <script src="https://hypothes.is/embed.js" async></script>
```

`translation/ch04-convex-problems.html` currently has no closing `</body>` tag, so append the same script at the end of that file without changing chapter text or adding unrelated structural fixes.

Do not add it to `translation/index.html` in this first pass, because the table of contents is not the reading surface.

- [ ] **Step 3: Run verification**

Run the PowerShell command from Step 1 again.

Expected: PASS with exit code 0 and no page names printed.

- [ ] **Step 4: Check script count**

Run:

```powershell
rg -n "https://hypothes.is/embed.js" translation
```

Expected: 15 matches, one per public reading page.

- [ ] **Step 5: Commit**

Run:

```powershell
git add docs/superpowers/plans/2026-06-30-hypothesis-annotations.md translation/*.html
git commit -m "Add public page annotations"
```
