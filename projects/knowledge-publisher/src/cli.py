"""Knowledge Publisher CLI：kp new / import / ls / check / build / preview"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

import typer

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from .parser import parse
from .renderer.douyin import DouyinRenderer
from .renderer.douyin_article import DouyinArticleRenderer
from .renderer.zhihu import build as build_zhihu
from .templates import load_project_config
from .validator import check_article, print_report

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "output"

app = typer.Typer(
    help="Knowledge Publisher（KP）— 一次创作，多平台输出：Markdown 母版 → 知乎发布包 + 抖音 PNG 图集",
    no_args_is_help=True,
    add_completion=False,
)

NEW_TEMPLATE = """---
title: __TITLE__
series: __SERIES__
author: __AUTHOR__
tags: []
---

# __TITLE__

## 开始写作

在这里写你的知识内容。母版支持：

- **粗体** 与 *斜体*、`行内代码`、[链接](https://example.com)
- 行内公式 $E=mc^2$ 与块公式
- 代码块、表格、引用、图片（放 assets/images/）

$$
E=mc^2
$$
"""


def _find_article(name: str) -> Optional[Path]:
    for p in (PROJECT_ROOT / "articles").glob("*/*.md"):
        if p.stem == name:
            return p
    return None


def _abort(msg: str) -> None:
    typer.echo(f"✗ {msg}", err=True)
    raise typer.Exit(1)


@app.command("new")
def new(name: str = typer.Argument(..., help="文章名（英文/拼音，如 bayes）"),
        category: str = typer.Option("math", "--category", "-c", help="文章分类目录"),
        author: Optional[str] = typer.Option(None, "--author", "-a", help="作者名（默认取 config/global.yaml）"),
        series: str = typer.Option("", "--series", "-s", help="所属系列")):
    """创建一篇新的 Markdown 母版。"""
    cat_dir = PROJECT_ROOT / "articles" / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    target = cat_dir / f"{name}.md"
    if target.exists():
        _abort(f"{target.relative_to(PROJECT_ROOT)} 已存在")
    cfg = load_project_config(PROJECT_ROOT)
    author = author or cfg.get("project", {}).get("default_author", "")
    title = name.replace("-", " ").replace("_", " ").title()
    content = (NEW_TEMPLATE
               .replace("__TITLE__", title)
               .replace("__SERIES__", series)
               .replace("__AUTHOR__", author))
    target.write_text(content, encoding="utf-8")
    typer.echo(f"✓ 已创建 {target.relative_to(PROJECT_ROOT)}")
    typer.echo(f"  下一步：kp check {name} && kp build {name} --all")


def save_imported_article(project_root: Path, name: str, category: str,
                          content: str) -> Path:
    """把导入的 Markdown 写入 articles/<category>/<name>.md；重名抛 ValueError。"""
    name = re.sub(r'[\\/:*?"<>|\s]+', "-", str(name).strip()).strip("-") or "untitled"
    category = (re.sub(r'[\\/:*?"<>|\s]+', "-", str(category).strip()).strip("-")
                or "math")
    cat_dir = project_root / "articles" / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    target = cat_dir / f"{name}.md"
    if target.exists():
        raise ValueError(f"已存在同名文章 {name}，请重命名后再导入")
    target.write_text(content, encoding="utf-8")
    return target


@app.command("import")
def import_article(path: str = typer.Argument(..., help="本地 Markdown 文件的路径"),
                   category: str = typer.Option("math", "--category", "-c",
                                                help="导入到哪个分类")):
    """从其他目录导入 Markdown 文件，统一管理。"""
    src = Path(path)
    if not src.is_file():
        _abort(f"找不到文件：{path}")
    if src.suffix.lower() not in (".md", ".markdown"):
        _abort("只支持 .md / .markdown 文件")
    content = src.read_text(encoding="utf-8", errors="replace")
    try:
        target = save_imported_article(PROJECT_ROOT, src.stem, category, content)
    except ValueError as e:
        _abort(str(e))
    typer.echo(f"✓ 已导入 → {target.relative_to(PROJECT_ROOT)}")
    typer.echo(f"  下一步：kp check {target.stem} && kp build {target.stem} --all")


@app.command("ls")
def ls():
    """列出所有文章。"""
    arts = sorted((PROJECT_ROOT / "articles").glob("*/*.md"))
    if not arts:
        typer.echo("（暂无文章，先运行 kp new <name>）")
        return
    for p in arts:
        try:
            doc, meta = parse(p.read_text(encoding="utf-8"))
            title = meta.get("title") or p.stem
        except Exception:
            title = p.stem
        typer.echo(f"  {p.parent.name:12s} {p.stem:24s} {title}")


@app.command("check")
def check(name: Optional[str] = typer.Argument(None, help="文章名；省略则检查全部")):
    """检查母版：Markdown / LaTeX / 图片 / 标题层级 / 段落密度。"""
    cfg = load_project_config(PROJECT_ROOT)
    if name:
        targets = [_find_article(name)] if name else []
    else:
        targets = sorted((PROJECT_ROOT / "articles").glob("*/*.md"))
    if name and not targets:
        _abort(f"未找到文章 {name}（articles/<分类>/{name}.md）")
    failed = False
    for p in targets:
        typer.echo(f"=== {p.relative_to(PROJECT_ROOT)} ===")
        report = check_article(p, PROJECT_ROOT, cfg)
        print_report(report)
        if report.errors:
            failed = True
    if failed:
        raise typer.Exit(1)


@app.command("build")
def build(name: str = typer.Argument(..., help="文章名"),
          platform: str = typer.Option("all", "--platform", "-p",
                                       help="zhihu | douyin(图文) | douyin-article(长文) | all"),
          all_platforms: bool = typer.Option(False, "--all", "-a",
                                             help="构建全部平台（等价 --platform all）"),
          template: str = typer.Option("default", "--template", "-t",
                                       help="抖音图文模板主题（templates/douyin/<theme>/）")):
    """构建发布包：知乎文章 + 抖音图文图集 + 抖音长文（公式转图片）。"""
    if all_platforms:
        platform = "all"
    if platform not in ("zhihu", "douyin", "douyin-article", "all"):
        _abort(f"未知平台 {platform}（可选 zhihu / douyin / douyin-article / all）")
    article = _find_article(name)
    if article is None:
        _abort(f"未找到文章 {name}，可先运行 kp new {name}")
    cfg = load_project_config(PROJECT_ROOT)
    report = check_article(article, PROJECT_ROOT, cfg)
    if report.errors:
        typer.echo("✗ 检查未通过，请先修复以下问题：")
        print_report(report)
        raise typer.Exit(1)
    for w in report.warnings:
        typer.echo(f"  ⚠ {w}")

    if platform in ("zhihu", "all"):
        result = build_zhihu(article, PROJECT_ROOT, OUTPUT_ROOT)
        typer.echo(f"✓ 知乎 → {result['html'].relative_to(PROJECT_ROOT)}")
        typer.echo(f"        {result['md'].relative_to(PROJECT_ROOT)}")
    if platform in ("douyin", "all"):
        renderer = DouyinRenderer(PROJECT_ROOT, OUTPUT_ROOT, template)
        files, pages, _ = renderer.build(article)
        typer.echo(f"✓ 抖音图文 → {files[0].parent.relative_to(PROJECT_ROOT)}（共 {len(files)} 页）")
        for f in files:
            typer.echo(f"        {f.name}")
    if platform in ("douyin-article", "all"):
        art_renderer = DouyinArticleRenderer(PROJECT_ROOT, OUTPUT_ROOT)
        result = art_renderer.build(article)
        typer.echo(f"✓ 抖音长文 → {result['html'].relative_to(PROJECT_ROOT)}（公式已转图片，浏览器全选复制即可粘贴到抖音）")
        typer.echo(f"        {result['md'].relative_to(PROJECT_ROOT)}")
    typer.echo("✓ 构建完成")


@app.command("preview")
def preview(name: Optional[str] = typer.Argument(None,
                                                 help="文章名（省略则打开文章列表首页）"),
            port: int = typer.Option(8765, "--port", help="预览服务端口"),
            theme: str = typer.Option("default", "--theme", "-t",
                                      help="初始抖音主题（default / tech-blue / black-gold ...）")):
    """启动本地预览：浏览器实时查看抖音图文效果（顶栏可切换主题）。"""
    if name is not None and _find_article(name) is None:
        _abort(f"未找到文章 {name}")
    from .preview import run_preview
    target = f"/preview/{name}?theme={theme}" if name else "/"
    typer.echo(f"预览服务启动：http://127.0.0.1:{port}{target}（Ctrl+C 退出）")
    run_preview(PROJECT_ROOT, name, port, theme=theme)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
