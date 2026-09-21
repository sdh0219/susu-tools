#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BiliNote 干净分发包导出工具。

从当前源目录复制可运行文件到输出目录，并自动排除：
  - 个人 Cookie / API Key / 数据库 / 日志 / 笔记结果 / 下载缓存
用法（在项目根目录）：
  python pack_dist.py
  python pack_dist.py --out D:\\Tools\\bilinote\\BiliNote_dist --slim
参数：
  --out     输出目录（默认：源目录同级 BiliNote_win_<ver>_dist）
  --slim    不打包 models/（Whisper 模型），体积更小，首次运行需联网下载
  --force   输出目录已存在时先删除再导出
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "BiliNote"
VERSION = "1.1.1"

# 绝不进入分发包（个人凭证与运行时私有数据）
NEVER_COPY_NAMES = {
    "cookies.txt",
    ".env",
    "bili_note.db",
    ".gitignore",
    ".git",
    ".vscode",
    ".idea",
    "__pycache__",
    "note_results",
    "logs",
    "pack_dist.py",
    "打包分发版.bat",
}

NEVER_COPY_SUFFIX = (
    ".pyc",
    ".pyo",
    ".log",
    ".db",
)

# 目录：始终排除内容（目录本身会按需重建空壳）
RUNTIME_DATA_DIRS = {
    "data",
    "note_results",
    "logs",
    "static/screenshots",
    "data/user_cookies",
}

# 分发包必须包含的顶层条目
INCLUDE_FILES = [
    "main.py",
    "ffmpeg_helper.py",
    "__init__.py",
    "requirements.txt",
    "Dockerfile",
    "Windows 运行.bat",
    "清理.md",
    "桌面端使用教程.html",
    ".env.example",
]

INCLUDE_DIRS = [
    "app",
    "events",
    "bin",
    "dist",
    "python310",
]

OPTIONAL_DIRS = [
    "models",
]


def _ignored(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    dir_path = Path(directory)
    for name in names:
        lower = name.lower()
        if name in NEVER_COPY_NAMES:
            ignored.add(name)
            continue
        if any(lower.endswith(sfx) for sfx in NEVER_COPY_SUFFIX):
            ignored.add(name)
            continue
        # 运行时数据目录整棵跳过
        rel = (dir_path / name).resolve()
        try:
            rel_s = str(rel.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            rel_s = ""
        if rel_s in RUNTIME_DATA_DIRS or rel_s.startswith("static/screenshots"):
            ignored.add(name)
            continue
        if name == "user_cookies":
            ignored.add(name)
    return ignored


def _dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def _fmt_mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


def write_clean_env(dest: Path) -> None:
    example = ROOT / ".env.example"
    env_path = dest / ".env"
    if example.exists():
        shutil.copy2(example, env_path)
    else:
        env_path.write_text(
            "BACKEND_PORT=8000\n"
            "BACKEND_HOST=127.0.0.1\n"
            "ENV=production\n"
            "OUT_DIR=./static/screenshots\n"
            "IMAGE_BASE_URL=/static/screenshots\n"
            "DATA_DIR=data\n"
            "FFMPEG_BIN_PATH=bin/\n"
            "COOKIE_FILE=\n"
            "TRANSCRIBER_TYPE=fast-whisper\n"
            "WHISPER_MODEL_SIZE=base\n",
            encoding="utf-8",
        )
    # 确保分发版不带个人 Cookie
    text = env_path.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if line.startswith("COOKIE_FILE="):
            lines.append("COOKIE_FILE=")
        elif line.startswith("COOKIES_FROM_BROWSER="):
            lines.append("# COOKIES_FROM_BROWSER=")
        elif line.startswith("BACKEND_HOST="):
            lines.append("BACKEND_HOST=127.0.0.1")
        else:
            lines.append(line)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_end_user_readme(dest: Path, with_models: bool) -> None:
    model_note = (
        "已内置 Whisper 模型，可离线转写。"
        if with_models
        else "未打包 models/，首次转写时会自动下载模型（需网络）。"
    )
    content = f"""# {APP_NAME} 使用说明（分发版）

## 启动

双击 **`Windows 运行.bat`**，浏览器会打开 `http://127.0.0.1:8000`。

{model_note}

## 首次使用（两步）

1. **配置模型供应商（必须）**  
   打开网页 → 供应商/模型设置 → 填入你自己的 API Key（DeepSeek / 通义 / OpenAI 兼容接口等）。  
   软件不自带任何模型密钥。

2. **B站 Cookie（可选）**  
   公开视频**无需 Cookie**，直接粘贴链接即可。  
   仅当提示需要登录 / 412 时，打开：  
   `http://127.0.0.1:8000/cookie.html`  
   按页面说明粘贴自己的 Cookie。Cookie 只保存在**你的电脑**上。

## 安全说明

- 默认只监听本机 `127.0.0.1`，局域网内他人无法访问。
- 请勿把本目录下的 `.env`、`*.db`、`cookies.txt`、`logs/` 发给他人。
- 若网页历史任务过多导致「生成失败」，参考《清理.md》清理浏览器缓存（笔记文件仍在 `note_results/`）。

## 打包信息

- 版本：{VERSION}
- 导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
- 本包已排除：个人 Cookie、模型 API Key、数据库、日志、历史笔记、下载缓存。
"""
    (dest / "使用说明.md").write_text(content, encoding="utf-8")


def ensure_runtime_dirs(dest: Path) -> None:
    for rel in [
        "data",
        "data/user_cookies",
        "note_results",
        "logs",
        "static",
        "static/screenshots",
    ]:
        (dest / rel).mkdir(parents=True, exist_ok=True)


def verify_clean(dest: Path) -> list[str]:
    """导出后自检：分发包内不应残留敏感文件。"""
    problems: list[str] = []
    banned_files = ["cookies.txt", "bili_note.db"]
    for name in banned_files:
        if (dest / name).exists():
            problems.append(f"发现不应存在的文件: {name}")
    env = dest / ".env"
    if env.exists():
        text = env.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("COOKIE_FILE=") and line.split("=", 1)[1].strip():
                problems.append(".env 中 COOKIE_FILE 仍非空")
            if line.startswith("COOKIES_FROM_BROWSER=") and not line.strip().startswith("#"):
                if line.split("=", 1)[1].strip():
                    problems.append(".env 中 COOKIES_FROM_BROWSER 仍启用")
            if line.startswith("BACKEND_HOST=") and "0.0.0.0" in line:
                problems.append(".env 中 BACKEND_HOST 不应为 0.0.0.0")
    # 不应包含历史笔记/日志内容
    for rel in ("note_results", "logs", "data"):
        d = dest / rel
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file() and p.stat().st_size > 0:
                    problems.append(f"运行时目录含数据文件: {p.relative_to(dest)}")
    # app 源码不应写死密钥
    for py in (dest / "app").rglob("*.py"):
        try:
            body = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "sk-" in body and "api_key" in body:
            # 允许变量名，禁止看起来像真实 key 的字面量
            for token in body.replace("\n", " ").split("\""):
                if token.startswith("sk-") and len(token) > 20:
                    problems.append(f"疑似硬编码密钥: {py.name}")
                    break
    return problems


def pack(out_dir: Path, slim: bool, force: bool) -> int:
    if not (ROOT / "main.py").exists():
        print("错误：请在 BiliNote 项目根目录运行本脚本。", file=sys.stderr)
        return 2

    out_dir = out_dir.resolve()
    if out_dir == ROOT:
        print("错误：输出目录不能与源目录相同。", file=sys.stderr)
        return 2
    if out_dir.exists():
        if not force:
            print(f"错误：输出目录已存在：{out_dir}\n请加 --force 覆盖，或换 --out 路径。", file=sys.stderr)
            return 2
        print(f"删除已有输出目录: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"源目录: {ROOT}")
    print(f"输出到: {out_dir}")
    print(f"模式: {'slim（不含 models）' if slim else '完整（含 models/whisper）'}")

    copied: list[str] = []

    for name in INCLUDE_FILES:
        src = ROOT / name
        if not src.exists():
            print(f"  跳过缺失文件: {name}")
            continue
        shutil.copy2(src, out_dir / name)
        copied.append(name)

    for name in INCLUDE_DIRS:
        src = ROOT / name
        if not src.exists():
            print(f"  跳过缺失目录: {name}")
            continue
        print(f"  复制目录: {name} ...")
        shutil.copytree(src, out_dir / name, ignore=_ignored)
        copied.append(name + "/")

    if not slim:
        for name in OPTIONAL_DIRS:
            src = ROOT / name
            if not src.exists():
                print(f"  跳过缺失可选目录: {name}")
                continue
            print(f"  复制可选目录: {name} ...")
            shutil.copytree(src, out_dir / name, ignore=_ignored)
            copied.append(name + "/")

    write_clean_env(out_dir)
    write_end_user_readme(out_dir, with_models=not slim)
    ensure_runtime_dirs(out_dir)
    copied += [".env", "使用说明.md"]

    # 打包自检
    problems = verify_clean(out_dir)
    size = _dir_size(out_dir)
    print()
    print("======== 导出结果 ========")
    print(f"条目数: {len(copied)}")
    for item in copied:
        print(f"  + {item}")
    print(f"包体积: {_fmt_mb(size)}")
    print(f"启动:   {out_dir / 'Windows 运行.bat'}")
    print(f"说明:   {out_dir / '使用说明.md'}")
    if problems:
        print()
        print("!!!! 自检未通过 !!!!")
        for p in problems:
            print(f"  - {p}")
        return 1
    print()
    print("自检通过：未发现 Cookie / 数据库 / 日志 / 非空运行时数据。")
    print("提醒：请确认源目录中的 cookies.txt、.env、logs/、*.db 未被你手动拷入输出目录。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="导出 BiliNote 干净分发包")
    parser.add_argument(
        "--out",
        default=str(ROOT.parent / f"{APP_NAME}_win_{VERSION}_dist"),
        help="输出目录（默认与源目录同级）",
    )
    parser.add_argument("--slim", action="store_true", help="不打包 models/ 模型目录")
    parser.add_argument("--force", action="store_true", help="输出目录已存在时覆盖")
    args = parser.parse_args()
    return pack(Path(args.out), slim=args.slim, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
