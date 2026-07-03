# Annotation Entry And Giscus Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the loud annotation pill with a quiet side-note anchor and make the Giscus modal show reading context before the discussion iframe.

**Architecture:** Keep the existing static annotation loader. Update `annotations.js` to render better button labels, extract pair context, and build a richer modal. Update `annotations.css` to style the side-note anchor, context card, discussion shell, loading state, and mobile fallback.

**Tech Stack:** Plain JavaScript, static HTML, CSS, Giscus embed.

---

## File Structure

- Modify `translation/assets/annotations.js`
  - Button labels and accessible names.
  - Pair context extraction.
  - Modal HTML structure for context card, discussion header, external discussion link, and loading state.
  - Giscus default theme.
- Modify `translation/assets/annotations.css`
  - Side-note annotation anchor.
  - Mobile fallback.
  - Giscus modal context and discussion styles.
- Optionally modify `translation/giscus-config.json`
  - Only if the checked-in config pins `theme` to `light`; use `noborder_light` so the approved embedded preview is reflected by the published page.
- No new runtime dependencies.

## Task 1: Side-note Annotation Entry

**Files:**
- Modify: `translation/assets/annotations.js`
- Modify: `translation/assets/annotations.css`
- Test: browser/manual plus `node --check translation/assets/annotations.js`

- [ ] **Step 1: Write a failing text check for the current undesired marker**

Run:

```powershell
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern '💬 ' -SimpleMatch -Quiet; if ($?) { Write-Error 'old emoji marker still present'; exit 1 }
```

Expected: FAIL because the current code still uses the emoji marker.

- [ ] **Step 2: Update annotated button rendering**

In `translation/assets/annotations.js`, change the `giscusCount > 0` branch so the visible text is only the count and the accessible label names the action:

```js
button.classList.add("has-comments");
button.textContent = String(giscusCount);
button.setAttribute("aria-label", "打开 " + giscusCount + " 条批注");
pair.classList.add("has-annotations");
```

For `annotations.length > 0`, set:

```js
button.textContent = "批注 " + annotations.length;
button.setAttribute("aria-label", "打开 " + annotations.length + " 条站内批注");
```

For the default branch, set:

```js
button.textContent = "批注";
button.setAttribute("aria-label", "打开批注");
```

- [ ] **Step 3: Update side-note CSS**

In `translation/assets/annotations.css`, replace the current `.annotation-button.has-comments` visual treatment with an outside anchor:

```css
.annotation-button.has-comments {
  top: 10px;
  right: -25px;
  width: 22px;
  min-width: 22px;
  min-height: 42px;
  padding: 0;
  border: 1px solid #cbd8f7;
  border-left: 3px solid var(--accent);
  border-radius: 0 11px 11px 0;
  background: #fff;
  color: var(--accent);
  font-size: 11px;
  box-shadow: 0 1px 5px rgba(37, 99, 235, .10);
}

.pair.has-annotations::after {
  content: "";
  position: absolute;
  top: 10px;
  right: 0;
  width: 3px;
  height: 42px;
  border-radius: 3px 0 0 3px;
  background: var(--accent);
}
```

Keep hover and focus behavior visible.

- [ ] **Step 4: Add mobile fallback**

In the existing `@media (max-width: 760px)` block, add:

```css
.annotation-button.has-comments {
  top: 8px;
  right: 8px;
  width: 22px;
  min-width: 22px;
  min-height: 22px;
  border-left-width: 1px;
  border-radius: 50%;
}

.pair.has-annotations::after {
  display: none;
}
```

- [ ] **Step 5: Verify syntax and text marker**

Run:

```powershell
node --check translation/assets/annotations.js
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern '💬 ' -SimpleMatch
```

Expected: `node --check` exits 0 and the emoji search returns no matches.

- [ ] **Step 6: Commit**

```powershell
git add translation/assets/annotations.js translation/assets/annotations.css
git commit -m "Polish annotation entry markers"
```

## Task 2: Giscus Modal Reading Context

**Files:**
- Modify: `translation/assets/annotations.js`
- Modify: `translation/assets/annotations.css`
- Optional modify: `translation/giscus-config.json`
- Test: browser/manual plus `node --check translation/assets/annotations.js`

- [ ] **Step 1: Write a failing text check for the current technical-first modal**

Run:

```powershell
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'page: <code>' -SimpleMatch -Quiet; if ($?) { Write-Error 'technical meta still displayed first'; exit 1 }
```

Expected: FAIL because the modal still renders `page: <code>...`.

- [ ] **Step 2: Add pair summary extraction**

In `translation/assets/annotations.js`, add this helper near `giscusContainerHtml`:

```js
function pairSummary(pair) {
  function firstText(selector) {
    const node = pair.querySelector(selector);
    if (!node) return "";
    const text = node.textContent.replace(/\s+/g, " ").trim();
    return text.length > 180 ? text.slice(0, 177) + "..." : text;
  }
  return {
    en: firstText(".en"),
    zh: firstText(".zh")
  };
}
```

- [ ] **Step 3: Replace Giscus container HTML**

Change `giscusContainerHtml(term)` to accept `summary` and `config`:

```js
function giscusContainerHtml(term, summary, config) {
  const pairId = term.split("#").pop();
  return [
    '<section class="annotation-context">',
    '  <div class="annotation-context-top"><span>正在讨论的段落</span><span>' + escapeHtml(pageName) + " / " + escapeHtml(pairId) + "</span></div>",
    summary.en ? '  <p><span>原文：</span>' + escapeHtml(summary.en) + "</p>" : "",
    summary.zh ? '  <p><span>译文：</span>' + escapeHtml(summary.zh) + "</p>" : "",
    "</section>",
    '<section class="annotation-discussion">',
    '  <div class="annotation-discussion-head">',
    '    <h3 class="annotation-section-title">讨论</h3>',
    '    <a href="https://github.com/' + escapeHtml(config.repo) + '/discussions" target="_blank" rel="noopener">在 GitHub Discussions 打开</a>',
    "  </div>",
    '  <div class="annotation-giscus"><div class="annotation-loading"><span></span><span></span><span></span><p>正在连接 GitHub Discussions...</p></div></div>',
    "</section>"
  ].join("");
}
```

- [ ] **Step 4: Update modal open flow**

Change `openPairModal` to accept the actual pair element:

```js
function openPairModal(pairIndex, pair, items, config) {
  const modal = ensureModal();
  const term = pageName + "#pair-" + pairIndex;
  const missing = requiredConfigMissing(config);
  const summary = pairSummary(pair);
  modal.querySelector(".annotation-heading").textContent = "段落批注";
  ...
}
```

Update the click handler:

```js
button.addEventListener("click", function () {
  openPairModal(pairIndex, pair, annotations, config);
});
```

- [ ] **Step 5: Hide technical metadata from the primary modal**

In `openPairModal`, remove the `annotation-meta` string from `list.innerHTML`. Keep the setup branch showing the term when configuration is missing because that is diagnostic text.

- [ ] **Step 6: Use no-border Giscus theme**

In `loadGiscus`, change the theme fallback:

```js
script.setAttribute("data-theme", config.theme || "noborder_light");
```

If `translation/giscus-config.json` contains `"theme": "light"`, change it to:

```json
"theme": "noborder_light"
```

- [ ] **Step 7: Add modal context CSS**

Append these styles to `translation/assets/annotations.css` near the existing modal section:

```css
.annotation-context {
  display: grid;
  gap: 10px;
  border: 1px solid #d9e4fb;
  border-radius: 8px;
  background: linear-gradient(180deg, #f8fbff, #fff);
  padding: 14px 16px;
}

.annotation-context-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
  font-size: 12px;
}

.annotation-context p {
  margin: 0;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.7;
}

.annotation-context p span {
  color: var(--muted);
}

.annotation-discussion {
  border: 1px solid var(--rule-soft);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.annotation-discussion-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--rule-soft);
  background: #fcfcfb;
  padding: 12px 14px;
}

.annotation-discussion-head a {
  color: var(--accent);
  font-size: 12px;
  text-decoration: none;
}

.annotation-loading {
  padding: 12px;
  color: var(--muted);
  font-size: 13px;
}

.annotation-loading span {
  display: block;
  height: 12px;
  margin: 10px 0;
  border-radius: 999px;
  background: linear-gradient(90deg, #eef2f7 25%, #f7f9fb 37%, #eef2f7 63%);
}

.annotation-loading span:nth-child(1) { width: 72%; }
.annotation-loading span:nth-child(2) { width: 48%; }
.annotation-loading span:nth-child(3) { width: 84%; }
```

- [ ] **Step 8: Verify syntax and technical meta removal**

Run:

```powershell
node --check translation/assets/annotations.js
Select-String -LiteralPath 'translation/assets/annotations.js' -Pattern 'page: <code>' -SimpleMatch
```

Expected: `node --check` exits 0 and the meta search returns no matches.

- [ ] **Step 9: Browser verify**

Run a local static server:

```powershell
Set-Location translation
python -m http.server 8910 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8910/ch03-convex-functions.html#pair-171
```

Expected:

- `pair 171` opens the modal.
- The modal title is `段落批注`.
- A context card appears before the Giscus iframe.
- The discussion section shows a loading skeleton before Giscus finishes.
- On narrow viewport, the annotation anchor stays inside the paragraph and does not create horizontal scrolling.

- [ ] **Step 10: Commit**

```powershell
git add translation/assets/annotations.js translation/assets/annotations.css translation/giscus-config.json
git commit -m "Polish giscus annotation modal"
```
