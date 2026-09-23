# Projects

**发布轨**：自己创作或二次开发、可独立运行/分发的工具。

每个子目录是一个自包含项目，必须带有：

- `README.md` — 是什么、怎么跑、依赖、限制
- 许可证说明（自有 MIT / Apache-2.0 / 上游许可等）
- 本地运行时与密钥 **不得** 提交进 git

命名用 kebab-case；新工具直接在 `projects/` 下开工，孵化成熟需要独立身份时再迁出（见 `docs/architecture.md` Governance）。

## Index

| Project | Summary | Run |
|---------|---------|-----|
| [`bilinote/`](./bilinote/) | BiliNote Windows 增强版：视频 → 转写 → AI Markdown 笔记 | [`bilinote/Windows 运行.bat`](./bilinote/Windows%20%E8%BF%90%E8%A1%8C.bat) |
| [`knowledge-publisher/`](./knowledge-publisher/) | Markdown 母稿 → 知乎 / 抖音多平台发布包 | [`knowledge-publisher/启动系统.bat`](./knowledge-publisher/%E5%90%AF%E5%8A%A8%E7%B3%BB%E7%BB%9F.bat) |
| [`ppt-doctor/`](./ppt-doctor/) | PPT医生：AI 生成医学 PPT（Electron） | `npm run build && npm start` |
| [`qing-tong/`](./qing-tong/) | 千瞳：2D 视频 → 可交互 3D 场景 | [`qing-tong/scripts/start.ps1`](./qing-tong/scripts/start.ps1) |
| [`bg-skin/`](./bg-skin/) | VS Code 编辑器背景壁纸扩展 | VS Code 打开后 F5 调试 |

## Adding a project

```text
projects/
└── <tool-name>/
    ├── README.md
    ├── LICENSE | NOTICE
    ├── <source…>
    └── .gitignore   # exclude runtimes / secrets
```

保持「源码进仓库、运行时留本机」的边界，和 CS 侧常见 monorepo 习惯一致。
