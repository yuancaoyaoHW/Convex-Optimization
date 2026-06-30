# 批注远程上线 + 全局浏览 + 段落徽标 设计

## 背景

当前凸优化翻译站（`yuancaoyaohw.github.io/Convex-Optimization`）已实现基于 Giscus 的段落级批注弹窗系统，但存在两个阻断性问题导致远程无法使用，且缺少跨章节的批注浏览能力。

实测发现：

- 本地领先 `origin/main` 9 个 commit（`bd4262e`..`aa78753`），含全部 `annotations.js/css`、`giscus-config.json`、各章 HTML 引用。**这些 commit 未 push**，线上 HTML 里根本没有 `<script src="assets/annotations.js">` 引用。
- 即便 push，`.github/workflows/pages.yml` 的 "Prepare site" 步骤只复制 `*.html` + `assets/` + `.nojekyll` + `bv_cvxbook.pdf`，**漏复制 `giscus-config.json` 和 `annotations.json`**（这两个文件在 `translation/` 根目录、不在 `assets/` 下）。线上 `fetch("giscus-config.json")` 必 404，弹窗永远停在"Giscus 未配置"提示，Giscus iframe 永不加载。
- curl 实测线上（2026-06-30）：`giscus-config.json`、`annotations.json`、`assets/annotations.js`、`assets/annotations.css` 全部 404。线上无任何批注功能。

## 目标

用户诉求："支持在远程加上批注，然后能方便预览。" 拆解为三层：

- **A 层 修通上线**：push + 补 workflow 复制 → 线上批注按钮和 Giscus 立即生效
- **B 层 全局浏览页**：新增 `annotations.html`，列出所有章节×段落的批注清单，点击跳转到对应章节并自动打开弹窗
- **C 层 段落徽标**：有评论的 `.pair` 显示带数字的角标和左侧色条，扫读时一眼可见哪段有批注

"加完即见"由 Giscus 自带行为满足（iframe 提交评论后自动刷新显示），不单列工作。

## 总体架构

三层全部在现有静态站基础上扩展，不自建后端：

```
annotations.html (B层)
  └─ 遍历所有章节×段落 → 对每个 term 调 giscus-widget.getDiscussionCount
  └─ 渲染清单 [章节 | 段落 | 💬N | 跳转链接]
  └─ 点击 → 跳转 ch0X.html#pair-N

ch0X.html (C层)
  └─ annotations.js 加载时对每个 .pair 调 getDiscussionCount
  └─ count>0 → .pair 加 .has-annotations 类，角标显示 💬N
  └─ 点击角标/按钮 → 打开弹窗（现有行为）
```

**数据层（降级方案，2026-06-30 实测确认）**：纯静态索引，不查询评论数。实测发现 `giscus@1.6.0` 的 `GiscusWidget` 类无 `getDiscussionCount` 方法（类型定义里所有方法为 private，源码 grep 为空），GitHub GraphQL 需 token 且静态站暴露 token 不安全。因此 B 层只显示章节/段落静态索引（不显评论数），C 层不加徽标数字。点击条目跳转到对应章节页打开弹窗，评论内容在弹窗内的 Giscus iframe 里查看。

## A 层 — 修通上线

### 改动 1：补 workflow 复制

`.github/workflows/pages.yml` 的 "Prepare site" 步骤，在现有 `cp` 之后增加两行：

```yaml
      - name: Prepare site
        run: |
          mkdir -p _site
          find translation -maxdepth 1 -type f -name "*.html" -exec cp {} _site/ \;
          cp -R translation/assets _site/assets
          cp translation/.nojekyll _site/.nojekyll
          cp bv_cvxbook.pdf _site/bv_cvxbook.pdf
          cp translation/giscus-config.json _site/giscus-config.json
          cp translation/annotations.json _site/annotations.json
```

`giscus-config.json` 和 `annotations.json` 在 `translation/` 根目录、不在 `assets/` 下，必须显式复制。`annotations.html`（B 层产物）本身是 `*.html`，会被现有 `find` 命令复制，无需额外处理。

### 改动 2：push

本地 9 个 commit push 到 `origin/main`。push 会触发 `pages.yml`（因为改了 `translation/**`），Actions 自动重新部署，线上立即生效。

### 不做

- 不修改 `annotations.js` 的核心逻辑（A 层只修部署，逻辑改进留给 B/C 层）

### 验证

- push 后 curl 线上 `giscus-config.json`、`assets/annotations.js` 应返回 200
- 打开线上 ch03 页面应看到右上角"批注"按钮，点击应加载 Giscus 评论框（而非"未配置"提示）

## B 层 — 全局浏览页

### 新增文件

- `translation/annotations.html`：独立的批注总览页
- `translation/annotations-index.json`：章节×段落的静态索引
- `translation/assets/annotations-index.js`：浏览页的数据加载与渲染逻辑

### 页面结构

```
导航条：返回目录 | 章节快速跳
主体：
  按章节分组，每章一个 section
    标题：Chapter N 章名
    段落表格：[pair-N | 段落首句预览 | 💬N条 | 查看→]
```

### 数据来源 — Giscus getDiscussionCount

1. 页面加载 `annotations-index.json`，拿到"全部章节×段落"的 term 清单
2. 对每个 term，调用 `giscus-widget.getDiscussionCount(term)` 拿评论数
3. count > 0 的行显示💬N 并高亮；count = 0 的行灰显"暂无"
4. 点击"查看"链接 → `ch0X-xxx.html#pair-N`

term 格式 = `ch0X-xxx.html#pair-N`，与 `annotations.js` 的 `openPairModal` 构造的 term 一致。

### 段落首句预览

从对应章节 HTML 抽取该 `.pair` 的中文首句（构建时静态写入 `annotations-index.json`，不实时抓取）。

### 批量调用策略

Giscus widget 异步且对并发有限制。实现上串行 + 小批量（每 5 个一批）调用，避免触发限流。每条返回后增量更新对应行的 DOM。

### 跳转后自动开弹窗

`annotations.js` 增加监听：页面加载时若 URL 有 `#pair-N`，自动打开第 N 段的弹窗。这让从总览页跳转过来的体验连贯。

### annotations-index.json 结构

```json
{
  "pages": [
    {
      "page": "ch02-convex-sets.html",
      "title": "Chapter 2 Convex Sets · 凸集",
      "pairs": [
        {"n": 1, "preview": "设 $x_1 \\ne x_2$ 为 $\\mathbb{R}^n$ 中的两个点..."},
        {"n": 2, "preview": "把 $y$ 写成..."}
      ]
    }
  ]
}
```

构建脚本从各章 HTML 自动抽取 `.pair` 数量和每段中文首句，生成此文件。章节增减时重跑脚本即可。preface + ch01–ch11 + appendix-a/b/c 共 14 个页面。

### 不做

- 不用 GitHub Discussions GraphQL API（需 token，静态站不适合）
- 不实时抓取评论内容摘要（getDiscussionCount 只给数量，摘要留给弹窗内的 Giscus iframe 显示）

## C 层 — 段落徽标（降级后不实施）

原始 C 层方案依赖 `getDiscussionCount` 查评论数显示徽标数字。2026-06-30 实测确认该 API 不存在于 `giscus@1.6.0`（见"总体架构"数据层说明）。用户已选择降级方案，**C 层不实施**。

C 层唯一保留的能力——"从浏览页跳转后自动开弹窗"——作为 B 层跳转链路的一部分实现（见 B 层"跳转后自动开弹窗"）。

## 错误处理与边界

### 网络/Giscus 失败

- `getDiscussionCount` 调用失败（网络超时、Giscus 服务不可用）→ 静默降级，该 pair 不加徽标，按钮保持"批注"文字。控制台不刷错误。
- 全局浏览页（B 层）若全部 `getDiscussionCount` 失败 → 显示"无法加载评论数据，请稍后刷新"，但仍显示章节/段落索引（静态部分），点击跳转仍可用。

### term 索引漂移（已知风险，本次不修）

当前 term 用 `querySelectorAll(".pair")` 的 DOM 顺序索引。将来在前面插入/删除一个 `.pair`，所有后续 term 平移，已有 Giscus discussion 会错挂到别的段落。本次设计不修这个（属于既有问题，修需要给每个 `.pair` 加稳定 id，改动面大），记录为已知风险，留待后续迭代。

### 配置缺失保护（已有）

`annotations.js` 的 `requiredConfigMissing` 检查 `repo/repoId/category/categoryId`，缺任一就显示 setup 提示而不加载 Giscus。A 层修上线后配置已完整，此分支不再触发，但保留作为防御。

### 空 annotations.json

当前 `annotations.json` 只有 `[]`。站内批注为空时，弹窗的"站内批注"section 不渲染（`staticAnnotationHtml` 对空数组返回空字符串），直接显示 Giscus section。行为正确，无需改。

### 移动端

现有 `annotations.css` 已有 `@media (max-width: 760px)` 适配。C 层新增的 `.has-annotations` 左侧色条在移动端仍适用，不额外处理。B 层浏览页用响应式表格，窄屏时转为卡片堆叠。

## 测试与验证

### A 层（修通上线）

- workflow 复制后，Actions 重新部署
- curl 线上验证：
  - `giscus-config.json` 返回 200 且内容含 `repoId`
  - `annotations.json` 返回 200
  - `assets/annotations.js` 和 `assets/annotations.css` 返回 200
- 浏览器打开线上 ch03，确认右上角出现"批注"按钮，点击后弹窗显示 Giscus 评论框（非"未配置"提示）

### B 层（全局浏览页）

- 本地 `python -m http.server 8910` 后访问 `/annotations.html`
- 页面列出全部 14 个章节（preface + ch01–ch11 + appendix-a/b/c）
- 每章下展开段落列表，count > 0 的行显示💬N
- 点击某行 → 跳转到对应章节页，URL 带 `#pair-N`，弹窗自动打开
- 全部 `getDiscussionCount` 失败时（断网模拟）→ 显示提示但章节索引仍在

### C 层（段落徽标）

- 本地打开某章页面
- 有评论的 `.pair` 显示左侧色条 + 实心"💬 N"按钮
- 无评论的 `.pair` 保持原样
- 查询失败的 pair 不影响其他 pair 的徽标渲染
- `node --check translation/assets/annotations.js` 通过

### 回归

- 现有弹窗打开/关闭、Esc 关闭、点击遮罩关闭、MathJax 重新排版等行为不受影响
- 站内批注（annotations.json）渲染逻辑不变

### 不做的测试

- 不写自动化测试框架（静态站，手动浏览器验证足够）
- 不做跨浏览器兼容矩阵（目标用户用现代浏览器）

## 不做（全局）

- 不自建后端
- 不把访客批注写进 `annotations.json`
- 不保留 Hypothes.is
- 不手写或猜测 `repoId/categoryId`
- 不修 term 索引漂移问题（已知风险，留待后续）
- 不做内联展开（C2）和右侧侧栏（C3）

## 官方依据

Giscus 是基于 GitHub Discussions 的评论系统，不需要数据库，评论数据存储在 GitHub Discussions 中；它会基于 URL、pathname、title 或指定 term 查找 discussion，找不到时可在首次评论时创建。`giscus-widget` custom element 提供 `getDiscussionCount(term)` 方法返回 `Promise<number>`，用于在不加载完整 iframe 的情况下查询某 term 的评论数。
