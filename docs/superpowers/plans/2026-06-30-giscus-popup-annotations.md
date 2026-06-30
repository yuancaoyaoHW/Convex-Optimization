# Giscus Popup Annotations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace JSON-export authoring with paragraph-level Giscus popup annotation entry points.

**Architecture:** Add `translation/giscus-config.json` for real Giscus settings. Update `annotations.js` so every `.pair` opens a modal for that page/pair; the modal shows existing static annotations when present and then lazy-loads Giscus when config is complete. If required config fields are empty, the modal shows a setup message instead of loading a broken iframe.

**Tech Stack:** Static HTML, vanilla JavaScript, CSS, Giscus, PowerShell/browser verification.

---

### Task 1: Verify Giscus Mode Is Missing

**Files:**
- Test only: `translation/assets/annotations.js`

- [ ] **Step 1: Run missing-feature check**

```powershell
if (Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'giscus-config.json' -SimpleMatch -Quiet) { exit 0 }
'missing giscus config loader'
exit 1
```

Expected: FAIL with `missing giscus config loader`.

### Task 2: Add Giscus Configuration File

**Files:**
- Create: `translation/giscus-config.json`

- [ ] **Step 1: Create config file**

Create `translation/giscus-config.json` with known repo value and empty Giscus IDs:

```json
{
  "repo": "yuancaoyaoHW/Convex-Optimization",
  "repoId": "",
  "category": "",
  "categoryId": "",
  "theme": "light",
  "lang": "zh-CN",
  "reactionsEnabled": "1",
  "emitMetadata": "0",
  "inputPosition": "bottom"
}
```

### Task 3: Update Popup Behavior

**Files:**
- Modify: `translation/assets/annotations.js`
- Modify: `translation/assets/annotations.css`

- [ ] **Step 1: Update JavaScript**

Update `annotations.js` to:

- fetch `annotations.json` and `giscus-config.json`;
- attach one `批注` button to every `.pair`;
- compute term as `<page>#pair-<n>`;
- open a modal showing page/pair metadata;
- render existing static annotations for the pair if any;
- load Giscus only when `repo`, `repoId`, `category`, and `categoryId` are non-empty;
- show a setup notice when config is incomplete.

- [ ] **Step 2: Update CSS**

Update `annotations.css` to:

- keep the existing modal styles;
- add `.annotation-giscus`, `.annotation-setup`, and `.annotation-term` styles;
- remove authoring form-only styles if unused.

### Task 4: Verify And Commit

**Files:**
- Test: `translation/assets/annotations.js`
- Test: `translation/assets/annotations.css`
- Test: `translation/giscus-config.json`

- [ ] **Step 1: Static checks**

```powershell
node --check 'translation/assets/annotations.js'
Get-Content -LiteralPath 'translation/giscus-config.json' -Raw | ConvertFrom-Json | Out-Null
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'giscus-config.json' -SimpleMatch
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'giscus.app/client.js' -SimpleMatch
Select-String -LiteralPath 'translation/assets/annotations.css' -Pattern 'annotation-giscus' -SimpleMatch
```

Expected: all pass.

- [ ] **Step 2: Browser checks**

Open `http://127.0.0.1:8910/ch02-convex-sets.html`, verify:

- `.annotation-button` count equals `.pair` count;
- clicking the first button opens the modal;
- modal term is `ch02-convex-sets.html#pair-1`;
- with empty config, modal shows setup text and no Giscus iframe;
- console has no errors.

- [ ] **Step 3: Commit**

```powershell
git add docs/superpowers/plans/2026-06-30-giscus-popup-annotations.md translation/giscus-config.json translation/assets/annotations.js translation/assets/annotations.css
git commit -m "Add giscus popup annotation shell"
```
