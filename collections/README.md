# Collections

**收录轨**：vibecoding 过程中亲测好用的第三方工具。

## Canonical data

| File | Role |
|------|------|
| [`tools.json`](./tools.json) | 唯一数据源（source of truth） |

Web 端通过 `scripts/sync-catalog.ps1` 生成：

- `web/assets/js/catalog-data.js`（`window.SUSU_CATALOG`，双击本地 HTML 也能渲染）
- `web/assets/data/tools.json`（供 `fetch`）

## Add an entry

1. 在 `tools.json` 的 `tools` 数组追加对象（字段见 `docs/architecture.md`）
2. 运行：`powershell -File scripts/sync-catalog.ps1`
3. 提交 JSON 与生成物，推送后 Pages 自动发布

## Principles

- 只收录**亲自用过 / 验证过**的工具
- 优先免费或有可用免费层
- 描述用一句话说清「解决什么问题」
- 失效或收费化后将 `status` 标为 `deprecated`
