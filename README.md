# susu-tools

[![site](https://img.shields.io/badge/site-susu--2x9.pages.dev-8b5cf6)](https://susu-2x9.pages.dev/)
[![repo](https://img.shields.io/badge/GitHub-sdh0219%2Fsusu--tools-181717?logo=github)](https://github.com/sdh0219/susu-tools)

**Personal Vibecoding Toolkit Monorepo.**

收录 vibe coding 过程中亲测好用的工具，并发布自己创作 / 二次开发的工具。

- **Live site:** https://susu-2x9.pages.dev/
- **Repository:** https://github.com/sdh0219/susu-tools

## Mission

| Track | Meaning | Where |
|-------|---------|-------|
| **Collect** | 精选第三方工具，数据驱动的在线目录 | [`collections/`](./collections/) → [`web/`](./web/) |
| **Ship** | 自研 / 二开作品，可独立运行与分发 | [`projects/`](./projects/) |
| **Publish** | Cloudflare Pages 静态站点 | [`web/`](./web/) + [`wrangler.jsonc`](./wrangler.jsonc) |

## Repository layout

```text
susu-tools/
├── web/                 # Public site (Cloudflare Pages asset root)
│   ├── index.html       # Landing
│   ├── tools.html       # Tool directory UI
│   └── assets/          # css / js / data
├── collections/         # Curated third-party tools (canonical JSON)
│   └── tools.json
├── projects/            # First-party & forked tools
│   └── bilinote/        # BiliNote Windows enhanced
├── docs/                # Charter, architecture
├── scripts/             # Utility scripts (catalog sync, …)
├── wrangler.jsonc       # Cloudflare Pages assets → web/
└── README.md
```

Design rationale: see [`docs/architecture.md`](./docs/architecture.md).

## Quick start

### Browse the tool directory locally

```powershell
cd web
python -m http.server 5173
# open http://127.0.0.1:5173/tools.html
```

Or double-click `web/index.html` (catalog is inlined via `assets/js/catalog-data.js`).

### Add a curated tool

1. Edit [`collections/tools.json`](./collections/tools.json)（新增一条，含 `id/name/url/desc/category/tags`）
2. Sync deploy artifacts:

   ```powershell
   powershell -File scripts/sync-catalog.ps1
   ```

3. Commit & push；Cloudflare Pages 按 `web/` 发布

### Run a published project

```powershell
cd projects\bilinote
# see projects/bilinote/README.md
.\Windows 运行.bat
```

## Published projects

| Project | Description | Docs |
|---------|-------------|------|
| [bilinote](./projects/bilinote/) | BiliNote Windows 增强版：视频 → Whisper → LLM 中文 Markdown 笔记 | [README](./projects/bilinote/README.md) |

## Deploy (Cloudflare Pages)

| Setting | Value |
|---------|-------|
| Git repo | `sdh0219/susu-tools` |
| Pages project | `susu` → https://susu-2x9.pages.dev/ |
| Asset / output directory | **`web`** |
| Wrangler assets.directory | `web` |

> 仓库由 `susu` 改名为 `susu-tools` 后：域名不变。若 Pages 不再触发部署，在 CF 控制台重新连接仓库，并确认输出目录为 `web`。

## Naming

| Surface | Name |
|---------|------|
| Local folder | `susu-tools` |
| GitHub | [sdh0219/susu-tools](https://github.com/sdh0219/susu-tools) |
| Site | [susu-2x9.pages.dev](https://susu-2x9.pages.dev/) |

## Security

- Never commit API keys, cookies, `*.db`, personal notes
- Project runtimes (`python310/`, Whisper `models/`, `.env`) stay local — see `projects/bilinote/.gitignore`

## License

- Site content & catalog: © Susu
- `projects/bilinote/`: Apache-2.0 (modifications) + upstream MIT — see `projects/bilinote/NOTICE`
