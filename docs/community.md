# 社区层（GitHub 驱动，站点零后端）

站点是纯静态托管，社区能力全部架在 GitHub 上：仓库 Issues / Discussions / PR。
站点只负责"把入口放在读者眼前"。

## 组件清单

| 组件 | 位置 | 作用 |
|---|---|---|
| 评论区 | `web/assets/js/comments.js` | giscus 挂载 `#comments`，背后是 Discussions（`Announcements` 分类），按页面路径建讨论 |
| 共建页 | `web/contribute.html` | 四类贡献入口（预填 Issue 模板）+ 贡献流程 + 贡献者墙 + 两条红线 |
| Issue 模板 | `.github/ISSUE_TEMPLATE/` | `note-fix.yml` / `feature.yml` / `site-bug.yml` + `config.yml` 引导到 Discussions |
| 贡献指南 | `CONTRIBUTING.md` | 明确"笔记走 Issue、代码走 PR"（笔记页是生成产物，直接改会被覆盖） |
| 贡献者墙 | contribute.html 内联脚本 | GitHub Contributors API 实时拉取头像与提交数，失败静默降级 |

## giscus 配置（已写入 comments.js）

```js
repo:       sdh0219/susu-tools
repoId:     R_kgDOSu58MQ
category:   Announcements          // giscus 要求该类型，bot 才能自动建讨论
categoryId: DIC_kwDOSu58Mc4DL8ba
mapping:    pathname               // 一页一讨论
lang:       zh-CN
```

Discussions 已于 2026-11-25 通过 API 开启。

## ⚠️ 唯一未完成的手动步骤：安装 giscus App

**必须由仓库所有者在浏览器完成**（OAuth 授权，无法用 API 代做）：

1. 打开 https://github.com/apps/giscus
2. 点 **Install** → 选择 **Only select repositories** → 勾 `sdh0219/susu-tools`
3. 授权完成即生效，无需改代码

未安装时评论区会显示 giscus 的提示，且每页标题下始终有一行「直接去仓库讨论 →」兜底链接——不会出现空白区块。

## 给新页面挂评论

```html
<section class="note-comments">
  <h2>💬 讨论与纠错</h2>
  <p class="note-comments-hint">…<a href="https://github.com/sdh0219/susu-tools/discussions">直接去仓库讨论 →</a></p>
  <div id="comments"></div>
</section>
<script defer src="/assets/js/comments.js"></script>
```

笔记页由 `scripts/build_notes.py` 的 `PAGE_TEMPLATE` 统一生成，无需逐页添加。

## 主题联动

`comments.js` 监听 `data-theme` 变化并向 giscus iframe 发 `postMessage`，站点的明暗切换会同步评论区配色。

## 待定事项

- **许可协议**：目前 CONTRIBUTING.md 写明"转载注明出处、不得商用，完整协议待定"。若要正式开源，建议补 `LICENSE`（内容常用 CC BY-NC-SA 4.0，代码常用 MIT）——这是站点所有者的法律选择，不要替他决定。
