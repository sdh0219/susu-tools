# Projects

**发布轨**：自己创作或二次开发、可独立运行/分发的工具。

每个子目录是一个自包含项目，必须带有：

- `README.md` — 是什么、怎么跑、依赖、限制
- 许可证说明（自有 Apache-2.0 / 上游 MIT 等）
- 本地运行时与密钥 **不得** 提交进 git

## Index

| Project | Summary | Run |
|---------|---------|-----|
| [`bilinote/`](./bilinote/) | BiliNote Windows 增强版：视频 → 转写 → AI Markdown 笔记 | [`bilinote/Windows 运行.bat`](./bilinote/Windows%20%E8%BF%90%E8%A1%8C.bat) |

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
