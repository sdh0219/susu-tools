# susu-tools

[![site](https://img.shields.io/badge/site-susu--2x9.pages.dev-8b5cf6)](https://susu-2x9.pages.dev/)
[![repo](https://img.shields.io/badge/GitHub-sdh0219%2Fsusu--tools-181717?logo=github)](https://github.com/sdh0219/susu-tools)

**二次元主题的个人工具站 Monorepo。**

自己做工具，也写使用心得——站点只放两类东西：亲手做的开源作品，和用过之后写下的随笔。

- **Live site:** https://susu-2x9.pages.dev/
- **Repository:** https://github.com/sdh0219/susu-tools

## Mission

| Track | Meaning | Where |
|-------|---------|-------|
| **Ship** | 自研 / 二开作品，唯一开发与发布地 | [`projects/`](./projects/) |
| **随笔** | 工具使用理解与复盘，精品安利 | [`web/blog.html`](./web/blog.html) |
| **Publish** | Cloudflare Pages 二次元主题站点 | [`web/`](./web/) + [`wrangler.jsonc`](./wrangler.jsonc) |

## Repository layout

```text
susu-tools/
├── web/                       # Public site (Cloudflare Pages asset root)
│   ├── index.html             # Landing（我的作品 + 关于 + 联系）
│   ├── study.html             # 自习室（复习资料 / 课程笔记 / 开源作业）
│   ├── blog.html              # 工具随笔
│   ├── 404.html               # 品牌化 404
│   └── assets/                # css / js / img / data / files / voice / models
├── projects/                  # First-party works（唯一开发地）
│   ├── bilinote/
│   ├── knowledge-publisher/
│   ├── ppt-doctor/
│   ├── qing-tong/
│   └── bg-skin/
├── docs/                      # Charter + architecture
└── scripts/                   # secrets_scan / live2d 模型与语音脚本
```

## Quick start

本地预览站点：

```powershell
cd web
python -m http.server 5173
# open http://127.0.0.1:5173
```

看板娘资源再生成（一般用不到）：

```powershell
projects\bilinote\python310\python.exe scripts\fetch_live2d_models.py   # 拉取模型
projects\bilinote\python310\python.exe scripts\gen_live2d_voice.py      # 生成语音包
```

## Site features

- 暗色主题：星空闪烁 + 四芒星落 + 长尾流星 + 紫色鼠标轨迹
- 浅色主题（莫兰迪暖燕麦）：樱花飘落 + 粉色鼠标轨迹
- Live2D 看板娘（右下角）：点击说话，预录甜美语音（`assets/voice/`），库与模型全部自托管
- 自定义 404 / meta+OG / robots / sitemap / RSS

## Published projects

| Project | Description | Docs |
|---------|-------------|------|
| [bilinote](./projects/bilinote/) | BiliNote Windows 增强版：视频 → Whisper → LLM 中文 Markdown 笔记 | [README](./projects/bilinote/README.md) |
| [knowledge-publisher](./projects/knowledge-publisher/) | 一次创作多平台输出：Markdown 母稿 → 知乎文章 / 抖音长文 / 抖音图文 PNG 图集 | [README](./projects/knowledge-publisher/README.md) |
| [ppt-doctor](./projects/ppt-doctor/) | PPT医生：面向医生的 AI PPT 生成器，一句话主题 → 大纲 → 实时预览 → .pptx（Electron + 云端大模型） | [README](./projects/ppt-doctor/README.md) |
| [qing-tong](./projects/qing-tong/) | 千瞳：2D 视频 → 可交互 3D 场景，深度估计 + Three.js 自由视角（FastAPI + Depth Anything V2） | [README](./projects/qing-tong/README.md) |
| [bg-skin](./projects/bg-skin/) | VS Code 编辑器背景壁纸扩展：透明度/模糊/位置调节，按时段自动换预设，校验和修复 + 卸载还原 | [README](./projects/bg-skin/README.md) |

## 自习室（study.html）

课业产出：复习资料 / 课程笔记 / 开源作业。页面由 `assets/data/study.json` 驱动，
新增内容只改这一个文件，卡片样式复用原工具目录留下的 `tool-*` 体系。

```json
{
  "items": [
    {
      "type": "material",
      "course": "数据结构",
      "semester": "2026 秋",
      "title": "期末复习提纲",
      "desc": "按章节整理的知识点 + 常考题型",
      "file": "/assets/files/ds-final-review.pdf",
      "format": "PDF",
      "size": "2.1 MB",
      "date": "2026-11-10",
      "tags": ["期末", "手写笔记"]
    }
  ]
}
```

- `type`：`material`（复习资料）/ `notes`（课程笔记）/ `homework`（开源作业）
- 资料类填 `file`，作业类填 `repo`；两者都没有时卡片不可点，适合先占位
- 小于 10MB 的文件放 `web/assets/files/`；更大的走 GitHub Releases，`file` 填完整 URL
- 红线：不上传老师课件 / 教材 / 真题原卷；作业开源前确认课程规定并清除个人信息

### 笔记页（web/notes/）

自习室的长文档以图文页呈现：源 md 在仓库外 `study_of_yuan/1_learning/rivew-应大/`（不进仓库），
`python scripts/build_notes.py` 一键转成 `web/notes/<slug>.html` + 同名 `.md` 下载副本。
改了源 md 后重跑脚本即可；新文档要在脚本里的映射表加一行，再到 `study.json` 加卡片。

### 思维导图（mindmap.html）

- 交互式 markmap：点击节点折叠 / 展开，滚轮缩放，拖拽平移，支持 `?m=<id>` 直达
- 依赖全部自托管：`assets/js/markmap-bundle.js`（markmap-lib + markmap-view + d3，esbuild 打包）
- 数据源 `assets/mindmaps/<slug>.md`（构建时剥离 mermaid 块）+ 清单 `assets/data/mindmaps.json`
- 新增导图：把新 md 剥掉 mermaid 代码块放进 `assets/mindmaps/`，清单加一行，`study.json` 加卡片

## Deploy (Cloudflare Pages)

| Setting | Value |
|---------|-------|
| Git repo | `sdh0219/susu-tools` |
| Pages project | `susu` → https://susu-2x9.pages.dev/ |
| Asset / output directory | **`web`** |

> 仓库改名 / Pages 不触发部署时：CF 控制台重新连接仓库，确认输出目录为 `web`。

## Security

- Never commit API keys, cookies, `*.db`, personal notes
- Project runtimes (`python310/`, Whisper `models/`, `node_modules/`, `.venv/`) stay local

## License

- Site content & own projects: © Susu（各项目目录内含各自 LICENSE）
- `projects/bilinote/`: Apache-2.0 (modifications) + upstream MIT — see `projects/bilinote/NOTICE`
