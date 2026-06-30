# 批注远程浏览页（降级方案）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为已上线的 Giscus 段落批注系统增加一个全局浏览页，列出全部 15 个章节×2359 个段落的索引，点击跳转到对应章节并自动打开该段弹窗。

**Architecture:** 纯静态站点增量，不查询评论数（Giscus 无此 API）。构建脚本 `build_annotations_index.py` 从各章 HTML 抽取 `.pair` 数量和中文首句，生成 `annotations-index.json`。浏览页 `annotations.html` 加载该 JSON 渲染折叠式清单（章节默认折叠，点开显示段落表格）。`annotations.js` 增加 hash 监听，URL 含 `#pair-N` 时自动打开第 N 段弹窗。

**Tech Stack:** 静态 HTML，vanilla JavaScript，CSS，Python 构建脚本。无 npm 依赖。

## Global Constraints

- 纯静态站，无后端，无 token，不查询 Giscus 评论数（实测 `getDiscussionCount` API 不存在于 `giscus@1.6.0`）
- 文件路径基于 `C:\Users\hw\Documents\凸优化\translation\`
- 现有 `annotations.js` 的弹窗逻辑保留不动，只追加 hash 监听
- Git 提交身份 yuancaoyaoHW
- 中英对照站，正文含 MathJax 公式

## File Structure

- 新增 `translation/_build_annotations_index.py` — 构建脚本：扫描各章 HTML，生成 index.json
- 新增 `translation/annotations-index.json` — 静态索引数据（构建产物，提交入库）
- 新增 `translation/annotations.html` — 浏览页骨架
- 新增 `translation/assets/annotations-index.js` — 浏览页渲染逻辑
- 改 `translation/assets/annotations.css` — 追加浏览页样式
- 改 `translation/assets/annotations.js` — 追加 hash 监听自动开弹窗
- 改 `.github/workflows/pages.yml` — 已在 A 层修好（`*.html` 和 `assets/` 已覆盖，无需再改）

---

### Task 1: 构建脚本生成 annotations-index.json

**Files:**
- Create: `translation/_build_annotations_index.py`
- Create: `translation/annotations-index.json`（产物）

**Interfaces:**
- Produces: `annotations-index.json`，结构：
```json
{
  "pages": [
    {"page": "ch02-convex-sets.html", "title": "Chapter 2 ...", "pairs": [{"n":1,"preview":"..."}, {"n":2,"preview":"..."}]}
  ]
}
```
- `pairs[].n` 从 1 开始，与 `annotations.js` 的 `pairIndex = index + 1` 一致
- `pairs[].preview` 取该 `.pair` 内 `.zh` 的第一个 `<p>` 或 `<h2>/<h3>` 文本前 70 字

**章节顺序**（写死在脚本里）：preface, ch01-introduction, ch02-convex-sets, ch03-convex-functions, ch04-convex-problems, ch05-duality, ch06-approximation, ch07-statistical-estimation, ch08-geometric-problems, ch09-unconstrained, ch10-equality-constrained, ch11-interior-point, appendix-a, appendix-b, appendix-c

- [ ] **Step 1: 写构建脚本**

```python
import re, os, json

BASE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["preface","ch01-introduction","ch02-convex-sets","ch03-convex-functions",
         "ch04-convex-problems","ch05-duality","ch06-approximation","ch07-statistical-estimation",
         "ch08-geometric-problems","ch09-unconstrained","ch10-equality-constrained",
         "ch11-interior-point","appendix-a","appendix-b","appendix-c"]

def extract_pairs(html):
    pairs = []
    chunks = re.split(r'(?=<div class="pair)', html)
    n = 0
    for chunk in chunks:
        if not re.match(r'<div class="pair', chunk):
            continue
        n += 1
        preview = "(无内容)"
        zh_m = re.search(r'<div class="zh">(.*?)</div>\s*</div>', chunk, re.S)
        if zh_m:
            zh = zh_m.group(1)
            pm = re.search(r'<(?:p|h[23456])[^>]*>(.*?)</(?:p|h[23456])>', zh, re.S)
            if pm:
                text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
                text = text.replace('\n',' ').replace('\r','')
                preview = text[:70] if text else "(空)"
        else:
            preview = "(图/无中文)"
        pairs.append({"n": n, "preview": preview})
    return pairs

pages = []
for stem in ORDER:
    fn = stem + ".html"
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        print("MISSING:", fn)
        continue
    html = open(p, encoding="utf-8").read()
    m = re.search(r'<title>(.*?)</title>', html)
    title = m.group(1) if m else fn
    pages.append({"page": fn, "title": title, "pairs": extract_pairs(html)})

out = {"pages": pages}
with open(os.path.join(BASE, "annotations-index.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("pages:", len(pages), "total pairs:", sum(len(p["pairs"]) for p in pages))
```

- [ ] **Step 2: 运行脚本生成 JSON**

Run: `cd translation && python _build_annotations_index.py`
Expected: 输出 `pages: 15 total pairs: 2359`（或接近），生成 `annotations-index.json`

- [ ] **Step 3: 验证 JSON**

Run: `python -c "import json; d=json.load(open('translation/annotations-index.json',encoding='utf-8')); print(len(d['pages'])); print(d['pages'][0]['page'], len(d['pages'][0]['pairs'])); print(d['pages'][0]['pairs'][0])"`
Expected: 打印 `15`、`preface.html 22`、`{'n': 1, 'preview': '本书讨论凸优化...'}`

- [ ] **Step 4: Commit**

```bash
git add translation/_build_annotations_index.py translation/annotations-index.json
git commit -m "Add annotations index builder and generated index"
```

---

### Task 2: 浏览页 HTML + CSS

**Files:**
- Create: `translation/annotations.html`
- Modify: `translation/assets/annotations.css`（追加，不改现有样式）

**Interfaces:**
- `annotations.html` 引用 `assets/annotations-index.js`（渲染）和 `assets/annotations.css`（样式）
- 复用现有 `--accent`/`--rule`/`--muted` 等 CSS 变量（来自 `bilingual.css`）

- [ ] **Step 1: 写 annotations.html**

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>批注总览 — Convex Optimization 中英对照</title>
  <link rel="stylesheet" href="assets/bilingual.css">
  <link rel="stylesheet" href="assets/annotations.css">
</head>
<body>
  <nav class="ann-nav">
    <a href="index.html">← 返回目录</a>
    <span class="ann-nav-title">批注总览</span>
  </nav>
  <main class="ann-overview">
    <p class="ann-hint">点击章节展开段落列表，再点段落直接跳转到该段的批注弹窗。</p>
    <div id="ann-list" class="ann-list">加载中…</div>
  </main>
  <script src="assets/annotations-index.js" defer></script>
</body>
</html>
```

- [ ] **Step 2: 追加浏览页 CSS 到 annotations.css**

在 `annotations.css` 末尾追加（不改动现有样式）：

```css
.ann-nav {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 22px;
  border-bottom: 1px solid var(--rule-soft);
  background: var(--panel);
}
.ann-nav a { color: var(--accent); text-decoration: none; font-size: 14px; }
.ann-nav-title { font-weight: 700; color: var(--ink); }
.ann-overview { max-width: 920px; margin: 0 auto; padding: 20px 22px 60px; }
.ann-hint { color: var(--muted); font-size: 14px; margin: 0 0 16px; }
.ann-list { display: grid; gap: 10px; }
.ann-chapter { border: 1px solid var(--rule-soft); border-radius: 8px; background: #fff; overflow: hidden; }
.ann-chapter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  font-weight: 600;
  color: var(--ink);
  user-select: none;
}
.ann-chapter-head:hover { background: var(--accent-soft); }
.ann-chapter-count { color: var(--muted); font-size: 13px; font-weight: 400; }
.ann-chapter-body { display: none; border-top: 1px solid var(--rule-soft); }
.ann-chapter.open .ann-chapter-body { display: block; }
.ann-pair-row {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  gap: 12px;
  align-items: baseline;
  padding: 8px 16px;
  border-bottom: 1px solid var(--rule-soft);
}
.ann-pair-row:last-child { border-bottom: none; }
.ann-pair-n { color: var(--muted); font-size: 13px; font-variant-numeric: tabular-nums; }
.ann-pair-preview { color: var(--ink); font-size: 14px; line-height: 1.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ann-pair-link { color: var(--accent); text-decoration: none; font-size: 13px; white-space: nowrap; }
.ann-pair-link:hover { text-decoration: underline; }
@media (max-width: 760px) {
  .ann-overview { padding: 14px; }
  .ann-pair-row { grid-template-columns: 36px 1fr; }
  .ann-pair-link { grid-column: 2; padding-top: 2px; }
}
```

- [ ] **Step 3: Commit**

```bash
git add translation/annotations.html translation/assets/annotations.css
git commit -m "Add annotation browse page HTML and styles"
```

---

### Task 3: 浏览页渲染 JS

**Files:**
- Create: `translation/assets/annotations-index.js`

**Interfaces:**
- Consumes: `annotations-index.json`（Task 1 产物），结构见 Task 1
- Produces: 渲染到 `#ann-list`，每段链接 `href="<page>#pair-<n>"`

- [ ] **Step 1: 写 annotations-index.js**

```javascript
(function () {
  const list = document.getElementById("ann-list");
  if (!list) return;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  fetch("annotations-index.json")
    .then(function (r) {
      if (!r.ok) throw new Error("load index failed");
      return r.json();
    })
    .then(function (data) {
      render(data.pages || []);
    })
    .catch(function (e) {
      list.textContent = "加载批注索引失败：" + e.message;
    });

  function render(pages) {
    const html = pages.map(function (page) {
      const pairs = (page.pairs || []).map(function (p) {
        return [
          '<div class="ann-pair-row">',
          '  <span class="ann-pair-n">#' + p.n + "</span>",
          '  <span class="ann-pair-preview">' + escapeHtml(p.preview) + "</span>",
          '  <a class="ann-pair-link" href="' + page.page + "#pair-" + p.n + '">查看 →</a>',
          "</div>"
        ].join("");
      }).join("");
      const count = (page.pairs || []).length;
      return [
        '<section class="ann-chapter">',
        '  <div class="ann-chapter-head">',
        "    <span>" + escapeHtml(page.title) + "</span>",
        '    <span class="ann-chapter-count">' + count + " 段</span>",
        "  </div>",
        '  <div class="ann-chapter-body">' + pairs + "</div>",
        "</section>"
      ].join("");
    }).join("");
    list.innerHTML = html;
    attachToggles();
  }

  function attachToggles() {
    document.querySelectorAll(".ann-chapter-head").forEach(function (head) {
      head.addEventListener("click", function () {
        head.parentElement.classList.toggle("open");
      });
    });
  }
})();
```

- [ ] **Step 2: 语法检查**

Run: `node --check translation/assets/annotations-index.js`
Expected: 无输出（通过）

- [ ] **Step 3: 本地浏览器验证**

Run: `cd translation && python -m http.server 8910 --bind 127.0.0.1`（后台），浏览器开 `http://127.0.0.1:8910/annotations.html`
Expected:
- 页面显示 15 个章节卡片
- 点击章节标题展开段落列表
- 每段显示序号 + 首句预览 + "查看 →"链接
- 链接 href 形如 `ch02-convex-sets.html#pair-5`

- [ ] **Step 4: Commit**

```bash
git add translation/assets/annotations-index.js
git commit -m "Add annotation browse page renderer"
```

---

### Task 4: hash 监听自动开弹窗

**Files:**
- Modify: `translation/assets/annotations.js`

**Interfaces:**
- Consumes: URL hash `#pair-N`（来自浏览页跳转链接）
- Produces: 页面加载时若有 `#pair-N`，自动点击第 N 个 `.pair` 的批注按钮（等按钮渲染后触发）

**关键约束**：`annotations.js` 现有逻辑在 `Promise.all` 完成后 `attachAnnotations` 才挂载按钮。hash 监听必须在按钮挂载后触发，不能在 DOMContentLoaded 时直接点（那时按钮还没渲染）。

- [ ] **Step 1: 在 annotations.js 末尾的 IIFE 内追加 hash 监听**

在现有 `Promise.all([...]).then(attachAnnotations)` 链之后，追加：

```javascript
  function openPairFromHash() {
    const m = /^#pair-(\d+)$/.exec(window.location.hash);
    if (!m) return;
    const n = Number(m[1]);
    const pairs = document.querySelectorAll(".pair");
    if (n < 1 || n > pairs.length) return;
    const btn = pairs[n - 1].querySelector(".annotation-button");
    if (btn) btn.click();
  }
```

然后把 `Promise.all` 链改为在 `attachAnnotations` 之后调用 `openPairFromHash`：

```javascript
  Promise.all([
    fetchJson(annotationsUrl),
    fetchJson(giscusConfigUrl)
  ]).then(function (results) {
    attachAnnotations(results[0], results[1]);
    openPairFromHash();
  });
```

- [ ] **Step 2: 语法检查**

Run: `node --check translation/assets/annotations.js`
Expected: 无输出（通过）

- [ ] **Step 3: 本地验证跳转链路**

浏览器开 `http://127.0.0.1:8910/ch03-convex-functions.html#pair-10`
Expected: 页面加载后第 10 段的批注弹窗自动打开，标题区显示 `page: ch03-convex-functions.html / pair: 10`

- [ ] **Step 4: 回归验证**

浏览器开 `http://127.0.0.1:8910/ch03-convex-functions.html`（无 hash）
Expected: 批注按钮正常显示，点击打开弹窗，Esc/遮罩关闭均正常（现有行为不变）

- [ ] **Step 5: Commit**

```bash
git add translation/assets/annotations.js
git commit -m "Auto-open annotation modal on #pair-N hash"
```

---

### Task 5: 部署与线上验证

**Files:**
- Test: 全部线上资源

- [ ] **Step 1: push 触发部署**

```bash
git push origin main
```

- [ ] **Step 2: 等待 Actions 完成后 curl 验证线上资源**

```bash
BASE=https://yuancaoyaohw.github.io/Convex-Optimization
for f in annotations.html annotations-index.json assets/annotations-index.js assets/annotations.js assets/annotations.css giscus-config.json; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' $BASE/$f)  $f"
done
```
Expected: 全部 200

- [ ] **Step 3: 浏览器验证线上完整链路**

打开 `https://yuancaoyaohw.github.io/Convex-Optimization/annotations.html`
Expected: 显示 15 章卡片，展开某章，点某段"查看→"跳转到章节页并自动开弹窗，弹窗内 Giscus 加载正常

- [ ] **Step 4: 验证 A 层遗留（批注按钮 + Giscus）**

打开线上 `ch03-convex-functions.html`
Expected: 右上角有"批注"按钮，点击弹窗显示 Giscus 评论框（非"未配置"提示）
