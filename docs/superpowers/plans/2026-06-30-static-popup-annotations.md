# Static Popup Annotations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Hypothes.is sidebar annotations with a static in-page popup annotation system.

**Architecture:** `translation/annotations.json` stores trusted annotation data keyed by page and `.pair` index. `translation/assets/annotations.js` loads the JSON, adds compact annotation buttons to matching `.pair` blocks, opens an accessible modal, and asks MathJax to typeset modal content. `translation/assets/annotations.css` styles the button and modal.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, MathJax, PowerShell verification.

---

### Task 1: Verify Current State Fails Target Contract

**Files:**
- Test only: `translation/*.html`

- [ ] **Step 1: Run target-contract verification before implementation**

```powershell
$pages = Get-ChildItem -LiteralPath 'translation' -Filter '*.html' | Where-Object { $_.Name -ne 'index.html' }
$missingCss = $pages | Where-Object { -not (Select-String -LiteralPath $_.FullName -Pattern 'assets/annotations.css' -SimpleMatch -Quiet) }
$missingJs = $pages | Where-Object { -not (Select-String -LiteralPath $_.FullName -Pattern 'assets/annotations.js' -SimpleMatch -Quiet) }
$hypothesis = $pages | Where-Object { Select-String -LiteralPath $_.FullName -Pattern 'https://hypothes.is/embed.js' -SimpleMatch -Quiet }
if ($missingCss -or $missingJs -or $hypothesis) {
  "missing_css=$($missingCss.Count)"
  "missing_js=$($missingJs.Count)"
  "hypothesis=$($hypothesis.Count)"
  exit 1
}
```

Expected: FAIL with nonzero counts because pages still use Hypothes.is and do not load the static popup assets.

### Task 2: Add Static Popup Assets

**Files:**
- Create: `translation/annotations.json`
- Create: `translation/assets/annotations.css`
- Create: `translation/assets/annotations.js`

- [ ] **Step 1: Create empty annotation data**

Create `translation/annotations.json`:

```json
[]
```

- [ ] **Step 2: Create popup styles**

Create `translation/assets/annotations.css` with styles for `.annotation-button`, `.annotation-modal`, `.annotation-panel`, `.annotation-close`, `.annotation-card`, and mobile layout.

- [ ] **Step 3: Create popup behavior**

Create `translation/assets/annotations.js` that:

- reads `annotations.json`;
- filters by `location.pathname` filename;
- assigns 1-based indices to `.pair` blocks;
- adds one button only when a pair has annotations;
- opens a modal with trusted annotation HTML;
- closes on backdrop, close button, or Escape;
- calls `MathJax.typesetPromise` for modal content when available.

### Task 3: Replace Page Includes

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

- [ ] **Step 1: Add stylesheet to each reading page**

Insert below the existing `assets/bilingual.css` stylesheet:

```html
  <link rel="stylesheet" href="assets/annotations.css">
```

- [ ] **Step 2: Replace Hypothes.is script**

Replace:

```html
  <script src="https://hypothes.is/embed.js" async></script>
```

with:

```html
  <script src="assets/annotations.js" defer></script>
```

`translation/ch04-convex-problems.html` has no closing `</body>`, so keep the script at the file end.

### Task 4: Verify And Commit

**Files:**
- Test: `translation/*.html`
- Test: `translation/annotations.json`

- [ ] **Step 1: Run target-contract verification**

Run the PowerShell verification from Task 1.

Expected: PASS with exit code 0 and no output.

- [ ] **Step 2: Validate JSON**

```powershell
Get-Content -LiteralPath 'translation/annotations.json' -Raw | ConvertFrom-Json | Out-Null
```

Expected: PASS with exit code 0.

- [ ] **Step 3: Count static includes**

```powershell
$html = Get-ChildItem -LiteralPath 'translation' -Filter '*.html' | Where-Object { $_.Name -ne 'index.html' }
$css = Select-String -LiteralPath ($html | ForEach-Object FullName) -Pattern 'assets/annotations.css' -SimpleMatch
$js = Select-String -LiteralPath ($html | ForEach-Object FullName) -Pattern 'assets/annotations.js' -SimpleMatch
$hypothesis = Select-String -LiteralPath ($html | ForEach-Object FullName) -Pattern 'https://hypothes.is/embed.js' -SimpleMatch
"css=$($css.Count)"
"js=$($js.Count)"
"hypothesis=$($hypothesis.Count)"
```

Expected: `css=15`, `js=15`, `hypothesis=0`.

- [ ] **Step 4: Commit**

```powershell
git add docs/superpowers/plans/2026-06-30-static-popup-annotations.md translation/annotations.json translation/assets/annotations.css translation/assets/annotations.js translation/*.html
git commit -m "Replace sidebar annotations with static popups"
```
