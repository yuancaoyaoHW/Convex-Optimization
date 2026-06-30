# 静态弹窗批注设计

## 目标

把当前 Hypothes.is 侧栏批注替换为站内静态弹窗批注，让 GitHub Pages 访客能看到更适合中文和公式的批注展示。

## 方案

批注数据放在 `translation/annotations.json`。阅读页加载 `assets/annotations.js` 和 `assets/annotations.css` 后，脚本按页面文件名和段落序号匹配批注。存在批注的 `.pair` 右上角显示一个“批注”按钮；点击按钮打开站内弹窗，显示该段的批注列表。

弹窗内容支持普通 HTML 片段，因此可以写段落、列表和 MathJax 公式。弹窗打开后调用 MathJax 对弹窗内容重新排版。

## 数据格式

`translation/annotations.json` 使用数组：

```json
[
  {
    "page": "ch02-convex-sets.html",
    "pair": 12,
    "title": "关于相对内部",
    "body": "<p>这里可以写中文解释，也可以写公式：$x \\in C$。</p>"
  }
]
```

字段含义：

- `page`：HTML 文件名。
- `pair`：该页面中第几个 `.pair`，从 1 开始。
- `title`：弹窗里显示的批注标题。
- `body`：批注正文，允许少量可信 HTML。

## 不做

- 不支持访客在线新增批注。
- 不自建后端、数据库或登录系统。
- 不再使用 Hypothes.is。
- 不改章节正文内容。

## 预计改动

- 新增 `translation/annotations.json`。
- 新增 `translation/assets/annotations.css`。
- 新增 `translation/assets/annotations.js`。
- 修改 15 个阅读页，移除 Hypothes.is 脚本，接入站内批注资源。

## 验证

- 检查 15 个阅读页均引入 `annotations.css` 和 `annotations.js`。
- 检查 15 个阅读页均不再引入 `https://hypothes.is/embed.js`。
- 检查 `annotations.json` 是合法 JSON。
- 本地启动静态服务，打开章节页确认无脚本错误；用临时批注数据检查弹窗和 MathJax 渲染，再恢复空批注数据。

## 后续可选增强

如果以后需要访客在线新增批注，可在保留弹窗展示的基础上接入 Giscus 或后端服务。
