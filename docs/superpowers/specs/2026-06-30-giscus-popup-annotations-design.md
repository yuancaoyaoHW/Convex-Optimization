# Giscus 弹窗批注设计

## 目标

把当前“生成 JSON 后手动合并”的批注编辑模式，升级为 GitHub Pages 上可随时新增、保存、公开可见的段落级批注。

## 方案

使用 Giscus 作为存储和评论层。页面仍保留站内弹窗体验：每个 `.pair` 显示一个“批注”入口，点击后打开宽弹窗，弹窗内懒加载该段对应的 Giscus 评论框。

每段批注映射到一个固定 discussion term：

```text
<page>#pair-<n>
```

例如：

```text
ch02-convex-sets.html#pair-12
```

Giscus 使用 `mapping="specific"` 和上述 term 查找或创建对应 GitHub Discussion。访客通过 GitHub OAuth 评论，数据保存在仓库的 GitHub Discussions 中。

## 必需配置

不能写假配置。实现必须集中读取以下真实配置：

- `repo`，例如 `owner/repo`
- `repoId`
- `category`
- `categoryId`

如果这些字段为空，弹窗显示配置提示，不加载 Giscus。

## 交互

- 普通模式下每段有一个轻量“批注”按钮。
- 点击按钮打开弹窗。
- 弹窗标题显示当前 `page` 和 `pair`。
- 配置完整时，弹窗内加载 Giscus。
- 配置缺失时，弹窗提示去 `https://giscus.app` 生成配置。

## 不做

- 不自建后端。
- 不把访客批注写进 `annotations.json`。
- 不保留 Hypothes.is。
- 不手写或猜测 `repoId/categoryId`。

## 验证

- 普通页面显示段落批注入口。
- 点击入口能打开站内弹窗。
- 配置缺失时显示明确提示，不加载错误 iframe。
- 配置完整后 Giscus iframe 的 `data-term` 对应当前段落。
- 控制台无脚本错误。

## 官方依据

Giscus 是基于 GitHub Discussions 的评论系统，不需要数据库，评论数据存储在 GitHub Discussions 中；它会基于 URL、pathname、title 或指定 term 查找 discussion，找不到时可在首次评论时创建。
