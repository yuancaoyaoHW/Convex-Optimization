# GitHub Pages 批注设计

## 目标

让 `translation` 静态站点在 GitHub Pages 上支持访客在线新增批注，并且尽量少改现有章节 HTML。

## 方案

先接入 Hypothes.is 作为公开批注层。它可以在静态网页上运行，访客登录 Hypothes.is 后可划词、选段并新增公开批注；其他访客打开同一 GitHub Pages 页面时也能看到这些公开批注。

## 不做

- 不自建后端。
- 不让前端直接写入 GitHub 仓库。
- 不把访客批注保存到 `annotations.json` 或章节 HTML。
- 不改章节正文内容。

## 预计改动

- 在 `translation/*.html` 页面底部统一加入 Hypothes.is 客户端脚本。
- 可选：在 `translation/index.html` 或页面顶部加入一句简短提示，说明批注功能由 Hypothes.is 提供。

## 数据流

访客在 GitHub Pages 页面中打开 Hypothes.is 侧边栏，登录后新增批注。批注内容保存在 Hypothes.is 服务中，并按页面 URL 关联显示。

## 取舍

优点：

- 改动小，适合静态站点。
- 不需要数据库、登录系统或部署后端。
- GitHub Pages 上可直接使用。

限制：

- 批注数据不在本仓库。
- 访客需要 Hypothes.is 账号。
- UI 由 Hypothes.is 提供，不能完全自定义。

## 验证

- 本地用 `translation/start-server.bat` 或 `python -m http.server` 打开页面。
- 检查章节页面加载后出现 Hypothes.is 侧边栏入口。
- 检查 MathJax 公式和双语排版不受影响。
- 检查 GitHub Pages 部署后的页面也能加载批注侧边栏。

## 后续可选增强

如果以后需要“站长精选批注”或“无需第三方账号的访客留言”，再单独设计：

- `annotations.json` 静态精选批注层。
- Supabase/Firebase/Cloudflare Worker 后端批注系统。
