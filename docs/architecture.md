# Architecture

## Why this layout

`susu-tools` is a **personal vibecoding toolkit monorepo** with two product tracks:

1. **Collect** — curated third-party tools published as a static directory site
2. **Ship** — first-party / forked tools that run locally and can be distributed

Separating *catalog data*, *web surface*, and *shipped projects* keeps each concern
independently reviewable — the way a CS-oriented repo should read at a glance.

```text
collections/tools.json  ──sync──►  web/assets  ──Cloudflare──►  susu-2x9.pages.dev
        ▲                                │
        │ edit                           │ link / mention
        │                                ▼
   (human curation)               projects/*  (run on laptop / package for others)
```

## Directory contracts

| Path | Contract |
|------|----------|
| `collections/` | **Source of truth** for curated tools. JSON only; no site chrome. |
| `web/` | **Deployable static site.** Only files needed by the browser. Cloudflare Pages asset root. |
| `web/assets/js/catalog-data.js` | Generated from `collections/tools.json` via `scripts/sync-catalog.ps1`. Do not hand-edit. |
| `web/assets/data/tools.json` | Same catalog copy for `fetch()` consumers. |
| `projects/` | **Shippable tools.** Each subproject has its own README, license notes, and runtime rules. |
| `docs/` | Charter + architecture; no runtime secrets. |
| `scripts/` | Repo utilities; PowerShell-first (Windows dev machine). |
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
- **Secrets**: never commit keys / cookies / `*.db` / runtimes; run `scripts/secrets_scan.py`
  before committing.

## Catalog schema

Each entry in `collections/tools.json` → `tools[]`:

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | kebab-case, unique |
| `name` | string | display name |
| `url` | string | absolute https URL |
| `desc` | string | one-line Chinese description |
| `icon` | string | emoji / glyph |
| `category` | enum | `ai` \| `dev` \| `design` \| `efficiency` \| `resource` \| `media` |
| `tags` | string[] | search keywords |
| `pricing` | enum | `free` \| `freemium` \| `paid` |
| `status` | enum | `active` \| `deprecated` |

## Change workflows

### Curate a tool

```text
edit collections/tools.json
  → powershell -File scripts/sync-catalog.ps1
  → commit web/assets/js/catalog-data.js + web/assets/data/tools.json
  → push → Pages deploys
```

### Publish a new project

```text
mkdir projects/<name>
  → add README.md (purpose, run, deps, license)
  → optional: wire a card into collections/ or web later
  → keep secrets/runtime out of git
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

- Not a package registry monorepo (no forced shared `package.json` workspace yet)
- Not committing multi-hundred-MB runtimes; those stay gitignored under each project
