# 批注入口与 Giscus 弹窗预览设计

## 目标

把章节页里的批注入口从醒目的胶囊按钮改成更适合长文阅读的边注式标记，并优化批注弹窗中 Giscus 的呈现，让它更像站内段落讨论，而不是直接嵌入外站评论表单。

## 背景

当前章节页由 `translation/assets/annotations.js` 给每个 `.pair` 添加 `.annotation-button`。当段落已有 Giscus 评论时，按钮显示为 `💬 N`，并给段落加 `.has-annotations`。样式定义在 `translation/assets/annotations.css`。

当前问题：

- `💬 N` 胶囊按钮颜色和形状太抢眼，会压住正文阅读节奏。
- Giscus 弹窗最先显示 `page / pair / term` 等技术信息，用户不容易立刻知道自己正在讨论哪段。
- Giscus 加载时只有空白高度，容易让人误以为坏了。

## 设计方向

### 批注入口

采用“外侧边注锚点”方案。

- 有评论的段落右侧显示一个窄数字锚点，例如 `1`。
- 段落右边缘显示一条短细线，把锚点和当前段落连接起来。
- 不显示 emoji。
- 无评论的段落仍可显示普通“批注”入口，样式应更克制。
- 移动端不使用外侧锚点，降级为右上角小圆点数字，避免横向溢出。

视觉标准：

- 默认状态像边注，不像操作按钮。
- 能扫读出哪里有批注。
- 不遮挡英文/中文正文。
- hover/focus 时可见且符合键盘可访问性。

### Giscus 弹窗

采用“阅读上下文 + 无边框讨论区”方案。

- 弹窗标题改为“段落批注”。
- 顶部显示章节与段落信息，例如“第 3 章 凸函数 · 第 171 段”。
- 在 Giscus 前增加“正在讨论的段落”卡片，展示该 `.pair` 中英文摘句。
- 隐藏默认展示的 `term` 技术细节；需要调试时可通过 DOM 或链接定位。
- Giscus 区块标题为“讨论”，右侧提供“在 GitHub Discussions 打开”的链接。
- Giscus 主题使用无边框浅色主题，减少框中框观感。
- Giscus iframe 加载前显示 skeleton 状态，而不是空白等待。

## 涉及文件

- 修改 `translation/assets/annotations.js`
  - 调整按钮文本与可访问标签。
  - 在打开弹窗时提取当前 `.pair` 的中英文段落摘要。
  - 改造 Giscus 容器 HTML，加入段落上下文、外链和加载状态。
  - 使用更适合嵌入的 Giscus 主题配置默认值。

- 修改 `translation/assets/annotations.css`
  - 重写 `.annotation-button.has-comments` 为外侧边注锚点。
  - 增加 `.pair.has-annotations` 的边缘 tether 样式。
  - 增加段落上下文卡片、讨论区容器、加载 skeleton 样式。
  - 增加移动端小圆点降级样式。

## 非目标

- 不改 Giscus 数据存储方式。
- 不改 GitHub Discussions 的 discussion term 规则。
- 不直接修改 Giscus iframe 内部 DOM。
- 不引入新前端依赖。

## 验证

- `node --check translation/assets/annotations.js`
- 本地静态服务打开 `translation/ch03-convex-functions.html`
- 验证有评论段落显示外侧数字锚点。
- 点击锚点后，弹窗先显示段落上下文，再显示 Giscus 讨论区。
- 窄屏下锚点不造成横向滚动。
- Giscus 未加载完成前显示 loading skeleton。

