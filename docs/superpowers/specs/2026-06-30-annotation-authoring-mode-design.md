# 批注前端编辑模式设计

## 目标

在静态弹窗批注系统上增加一个前端编辑模式，让站长可以直接在页面里选择段落并生成批注 JSON，避免手动数 `.pair` 序号。

## 进入方式

在阅读页 URL 后加查询参数：

```text
?annotate=1
```

例如：

```text
http://127.0.0.1:8910/ch02-convex-sets.html?annotate=1
```

## 交互

- 普通模式：只显示已有批注的“批注”按钮。
- 编辑模式：每个 `.pair` 右上角显示“+批注”按钮。
- 点击“+批注”后打开编辑弹窗，自动填入当前 `page` 和 `pair`。
- 用户填写标题和正文后，页面生成一段 JSON。
- 用户可以复制 JSON，或下载 `annotation-snippet.json`。

## 数据

生成的 JSON 是单条批注对象：

```json
{
  "page": "ch02-convex-sets.html",
  "pair": 1,
  "title": "标题",
  "body": "<p>正文，支持 MathJax：$x \\in C$。</p>"
}
```

前端不直接写 `translation/annotations.json`。用户复制或下载 JSON 后，手动合并进 `annotations.json` 并提交。

## 不做

- 不保存到浏览器本地存储。
- 不上传到服务器。
- 不修改 GitHub 仓库文件。
- 不支持访客公开提交。

## 验证

- 普通模式不显示“+批注”按钮。
- `?annotate=1` 模式显示每段“+批注”按钮。
- 点击按钮后 JSON 中的 `page` 和 `pair` 正确。
- 生成 JSON 可被 `ConvertFrom-Json` 解析。
