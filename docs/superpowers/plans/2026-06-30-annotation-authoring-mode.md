# Annotation Authoring Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `?annotate=1` front-end authoring mode that generates copyable annotation JSON for the current paragraph.

**Architecture:** Extend the existing static annotation JavaScript with an authoring mode branch. In authoring mode every `.pair` gets a `+批注` button that opens an editor modal and generates a single annotation object; CSS adds form, textarea, and output styling.

**Tech Stack:** Vanilla JavaScript, CSS, static HTML, PowerShell and browser verification.

---

### Task 1: Verify Feature Is Missing

**Files:**
- Test only: `translation/assets/annotations.js`

- [ ] **Step 1: Run missing-feature check**

```powershell
if (Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'get("annotate") === "1"' -SimpleMatch -Quiet) { exit 0 }
'missing annotate query mode'
exit 1
```

Expected: FAIL with `missing annotate query mode`.

### Task 2: Implement Authoring Mode

**Files:**
- Modify: `translation/assets/annotations.js`
- Modify: `translation/assets/annotations.css`

- [ ] **Step 1: Add CSS**

Add styles for `.annotation-add-button`, `.annotation-field`, `.annotation-input`, `.annotation-textarea`, `.annotation-output`, `.annotation-actions`, and `.annotation-copy-status`.

- [ ] **Step 2: Add JavaScript**

Update `annotations.js` so `new URLSearchParams(location.search).get("annotate") === "1"` enables authoring mode. In that mode each `.pair` receives a `+批注` button. Clicking opens an editor modal with title/body fields and generated JSON output. The modal supports copying JSON and downloading `annotation-snippet.json`.

### Task 3: Verify

**Files:**
- Test: `translation/assets/annotations.js`
- Test: `translation/assets/annotations.css`

- [ ] **Step 1: Run JavaScript syntax check**

```powershell
node --check 'translation/assets/annotations.js'
```

Expected: PASS.

- [ ] **Step 2: Run static grep checks**

```powershell
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'get("annotate") === "1"' -SimpleMatch
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'annotation-snippet.json' -SimpleMatch
Select-String -LiteralPath 'translation/assets/annotations.css' -Pattern 'annotation-add-button' -SimpleMatch
```

Expected: all commands find matches.

- [ ] **Step 3: Browser check**

Open `http://127.0.0.1:8910/ch02-convex-sets.html?annotate=1`, verify `+批注` buttons exist, click one, and confirm generated JSON includes `"page": "ch02-convex-sets.html"` and `"pair": 1`.

- [ ] **Step 4: Commit**

```powershell
git add docs/superpowers/plans/2026-06-30-annotation-authoring-mode.md translation/assets/annotations.js translation/assets/annotations.css
git commit -m "Add annotation authoring mode"
```
