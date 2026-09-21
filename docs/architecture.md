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
