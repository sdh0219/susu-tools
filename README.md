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
│   ├── index.html       # Landing (+ own-projects showcase)
│   ├── tools.html       # Tool directory UI
│   ├── blog.html        # 工具随笔 (essays on tool craft)
│   └── assets/          # css / js / data / img
├── collections/         # Curated third-party tools (canonical JSON)
│   └── tools.json
├── projects/            # First-party & forked tools
│   ├── bilinote/        # BiliNote Windows enhanced
│   ├── knowledge-publisher/  # One Markdown → Zhihu / Douyin publisher
│   ├── ppt-doctor/      # AI-powered medical PPT generator (Electron)
│   ├── qing-tong/       # 千瞳: 2D video → interactive 3D scene (Three.js + Depth Anything V2)
│   └── bg-skin/         # VS Code editor background wallpaper extension
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

```powershell
cd projects\knowledge-publisher
# see projects/knowledge-publisher/README.md
.\首次安装.bat   # 首次使用
.\启动系统.bat   # 日常启动
```

```powershell
cd projects\ppt-doctor
# see projects/ppt-doctor/README.md
npm install
npm run build
npm start        # 或 npm run package 打包 Windows 安装包
```

```powershell
cd projects\qing-tong
# see projects/qing-tong/README.md
.\scripts\setup.ps1   # 首次初始化
.\scripts\start.ps1   # 启动前后端
```

```powershell
cd projects\bg-skin
# see projects/bg-skin/README.md & INSTALL.md
# 开发：VS Code 打开目录后按 F5 运行扩展开发宿主
# 打包：npx vsce package  →  得到可安装的 .vsix
```

## Published projects

| Project | Description | Docs |
|---------|-------------|------|
| [bilinote](./projects/bilinote/) | BiliNote Windows 增强版：视频 → Whisper → LLM 中文 Markdown 笔记 | [README](./projects/bilinote/README.md) |
| [knowledge-publisher](./projects/knowledge-publisher/) | 一次创作多平台输出：Markdown 母稿 → 知乎文章 / 抖音长文 / 抖音图文 PNG 图集 | [README](./projects/knowledge-publisher/README.md) |
| [ppt-doctor](./projects/ppt-doctor/) | PPT医生：面向医生的 AI PPT 生成器，一句话主题 → 大纲 → 实时预览 → .pptx（Electron + 云端大模型） | [README](./projects/ppt-doctor/README.md) |
| [qing-tong](./projects/qing-tong/) | 千瞳：2D 视频 → 可交互 3D 场景，深度估计 + Three.js 自由视角（FastAPI + Depth Anything V2） | [README](./projects/qing-tong/README.md) |
| [bg-skin](./projects/bg-skin/) | VS Code 编辑器背景壁纸扩展：透明度/模糊/位置调节，按时段自动换预设，校验和修复 + 卸载还原 | [README](./projects/bg-skin/README.md) |

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
