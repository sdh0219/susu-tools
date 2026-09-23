# Architecture

## Why this layout

`susu-tools` 是一个**二次元主题的个人工具站 monorepo**，两类内容：

1. **Ship** — 自研 / 二开工具，`projects/` 是唯一开发与发布地
2. **随笔** — 工具使用理解与复盘，`web/blog.html`

站点本身（`web/`）部署在 Cloudflare Pages。第三方工具目录已于 2026-09 下架：
同质化高、无个人特色；精品安利改由随笔承载。

```text
projects/*  ──link/mention──►  web/index.html  ──Cloudflare──►  susu-2x9.pages.dev
                                    │
                                    ▼
                            blog.html（随笔）
```

## Directory contracts

| Path | Contract |
|------|----------|
| `web/` | **Deployable static site.** Only files needed by the browser. Cloudflare Pages asset root. |
| `web/assets/js/oml2d.min.js` + `web/assets/models/` | Live2D 看板娘自托管资源（库 + 4 个模型），勿手改 |
| `web/assets/voice/` | 看板娘预录语音包（p0~p8.mp3），缺失时只出气泡不出声 |
| `web/assets/js/live2d.js` | 看板娘加载器：位置 / 模型列表 / 交互与语音逻辑 |
| `web/assets/js/starfield.js` | 氛围层：暗色星空流星 / 浅色樱花，单帧异常不终止循环 |
| `projects/` | **Shippable tools.** 每个子项目自带 README、LICENSE、运行时规则 |
| `docs/` | Charter + architecture；no runtime secrets |
| `scripts/` | secrets_scan / live2d 模型下载 / 语音生成 |
| `wrangler.jsonc` | Pages config; `assets.directory` **must** stay `web`. |

## Project registry

| Project | What | Stack | Status |
|---------|------|-------|--------|
| `projects/bilinote/` | BiliNote Windows 增强版：视频 → Whisper → LLM 中文笔记 | Python + FastAPI | shipped |
| `projects/knowledge-publisher/` | Markdown 母稿 → 知乎 / 抖音多平台发布包 | Python + markdown-it | shipped |
| `projects/ppt-doctor/` | 医生 AI PPT 生成器：主题 → 大纲 → .pptx | Electron + React + TS | shipped |
| `projects/qing-tong/` | 千瞳：2D 视频 → 可交互 3D 场景 | FastAPI + Three.js | incubating |
| `projects/bg-skin/` | VS Code 编辑器背景壁纸扩展 | VS Code Extension (JS) | shipped |

## Governance

- **Single source of truth**: all first-party tools are developed *inside* this monorepo.
  Former standalone repos (knowledge-publisher, ppt_doctor, QingTong, bg-skin) are retired;
  never edit a retired copy. Full-history backups live as git bundles outside the repo.
- **Default home for new tools**: `projects/<kebab-case-name>/`. Incubate first, graduate later —
  promote to a standalone repo only when it needs its own identity / release channel / user base,
  carrying history via `git filter-repo`.
- **Releases**: tag + GitHub Release, named `<project>-v<semver>` (e.g. `bg-skin-v0.5.1`).
- **No generic tool directory**: 第三方工具不做目录收录；精品安利写进随笔。
- **Secrets**: never commit keys / cookies / `*.db` / runtimes; run `scripts/secrets_scan.py`
  before committing.

## Change workflows

### Publish a new project

```text
mkdir projects/<kebab-name>
  → add README.md (purpose, run, deps, license)
  → index.html 的「我的作品」加一张卡片
  → keep secrets & runtimes out of git
```

### Deploy topology

| Piece | Config |
|-------|--------|
| GitHub | `sdh0219/susu-tools` |
| Cloudflare Pages project name | `susu` (unchanged by repo rename) |
| Public URL | https://susu-2x9.pages.dev/ |
| Asset directory | `web` |

If rename breaks Git integration: CF Dashboard → project → Settings → Builds → reconnect repo → output dir `web`.

## Non-goals

- Not a package registry monorepo (no forced shared `package.json` workspace)
- Not committing multi-hundred-MB runtimes; those stay gitignored under each project
- 不重建第三方工具目录；不收录与二次元主题无关的泛推荐内容
