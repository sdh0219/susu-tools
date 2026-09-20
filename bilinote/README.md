# BiliNote Windows 增强版

基于 [JefferyHcool/BiliNote](https://github.com/JefferyHcool/BiliNote)（MIT）的 Windows 二次开发分支：  
粘贴 B 站 / YouTube / 抖音等视频链接 → 本地下载音视频 → Whisper 转写 → 调用大模型生成结构化中文 Markdown 笔记。

> **上游项目**：[JefferyHcool/BiliNote](https://github.com/JefferyHcool/BiliNote)  
> 本仓库保留上游版权与 MIT 声明；二次开发改动以 **Apache-2.0** 发布（见 `LICENSE` / `NOTICE`）。

## 本分支增强点

- **B 站 Cookie 无优先 + 用户自助配置**  
  公开视频不带 Cookie 直接下载；登录墙/412 时自动重试。使用者在 `http://127.0.0.1:8000/cookie.html` 自行粘贴 Cookie，不再依赖分发者个人账号。
- **本地安全加固**  
  默认仅监听 `127.0.0.1`；日志对 API Key 脱敏；Cookie 接口平台白名单。
- **干净分发打包**  
  `pack_dist.py` / `打包分发版.bat` 一键导出，自动排除 Cookie、`.env`、数据库、日志、历史笔记。
- **模型 Key BYOK**  
  网页里配置自己的 OpenAI 兼容 / DeepSeek / 通义等供应商，安装包不内置任何密钥。

## 在本仓库中的位置

本项目位于 monorepo 子目录 [susu/bilinote](https://github.com/sdh0219/susu/tree/main/bilinote)。
克隆后进入该目录再运行打包脚本或 main.py。

## 快速开始

### 方式一：便携运行包（推荐给使用者）

1. 使用本机运行 `打包分发版.bat`，或从 Release 下载分发包  
2. 双击包内 `Windows 运行.bat`  
3. 浏览器打开 `http://127.0.0.1:8000`  
4. 在网页「全局配置 / 供应商」中填入**自己的** API Key  
5. 粘贴视频链接生成笔记  
6. （可选）B 站需登录时打开 `http://127.0.0.1:8000/cookie.html`

### 方式二：源码环境

```bat
:: 依赖 Python 3.10+，并安装 requirements.txt
:: 需要本机 ffmpeg，或将 ffmpeg 放入 bin\
copy .env.example .env
python main.py
```

| 环境变量 | 说明 |
|---------|------|
| `BACKEND_PORT` | 后端端口，默认 8000 |
| `BACKEND_HOST` | 默认 `127.0.0.1`（仅本机）；改为 `0.0.0.0` 会对局域网开放，请自行评估风险 |
| `COOKIE_FILE` | 可选，Netscape cookies.txt 路径；**分发版请留空** |
| `TRANSCRIBER_TYPE` | 默认 `fast-whisper` |
| `WHISPER_MODEL_SIZE` | 默认 `base` |

## 安全与隐私

- **不要**把 `cookies.txt`、`.env`、`*.db`、`logs/` 提交到 Git 或发给他人  
- 使用者 Cookie 只保存在本机 `data/user_cookies/` 与本地 SQLite  
- 请遵守各视频平台服务条款与著作权法，仅处理你有权使用的内容  
- 打包脚本会自检：分发目录内不应出现 Cookie / 数据库 / 日志

## 目录结构（源码仓库）

```
app/            后端（FastAPI：下载 / 转写 / LLM / Cookie 配置）
events/         信号与事件处理
dist/           前端编译产物 + cookie 配置页
main.py         服务入口
pack_dist.py    干净分发包导出脚本
.env.example    无密钥环境变量模板
NOTICE          上游 MIT 归属说明
```

仓库**不包含**：`python310/`（便携 Python）、`bin/ffmpeg.exe`、`models/`（Whisper 权重）、运行数据。  
便携包构建请在本机准备上述依赖后执行打包脚本。

## 打包

```bat
打包分发版.bat
:: 或
python pack_dist.py --out ..\BiliNote_dist --force
python pack_dist.py --out ..\BiliNote_dist_slim --slim --force
```

## 说明与限制

- 前端目前仅有 `dist/` 编译产物，**无前端源码**；UI 改动需到上游仓库获取  
- Cookie 配置入口：`/cookie.html`（主界面暂无按钮）  
- 大会员 / 强风控视频仍可能下载失败  
- 前端 localStorage 满时参考 `清理.md`

## 致谢

感谢 [JefferyHcool/BiliNote](https://github.com/JefferyHcool/BiliNote) 及所有上游贡献者提供原始项目。

## License

- 本仓库二次开发改动：[Apache-2.0](./LICENSE)  
- 上游 BiliNote：MIT（版权说明见 [NOTICE](./NOTICE)）
