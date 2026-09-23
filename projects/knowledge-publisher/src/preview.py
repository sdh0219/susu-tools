"""本地预览服务：kp preview。

基于 FastAPI：一边修改 Markdown、一边在浏览器里看抖音最终效果。
同时提供在线编辑器（/edit）、保存重建（/api/article/*）、使用指南（/guide）。
"""
from __future__ import annotations

import io
import json
import re
import shutil
import threading
import webbrowser
import zipfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .ast_nodes import Heading, plain_text
from .cli import NEW_TEMPLATE, save_imported_article
from .parser import parse
from .renderer.douyin import DouyinRenderer
from .renderer.douyin_article import DouyinArticleRenderer
from .renderer.zhihu import build as build_zhihu

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def _scan_articles(root: Path) -> List[dict]:
    arts = []
    for p in sorted((root / "articles").glob("*/*.md")):
        try:
            doc, meta = parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = str(meta.get("title") or "").strip()
        if not title:
            for b in doc.children:
                if isinstance(b, Heading) and b.level == 1:
                    title = plain_text(b.children).strip()
                    break
        arts.append({"name": p.stem, "category": p.parent.name, "title": title or p.stem})
    return arts


def _available_themes(root: Path) -> List[str]:
    """扫描 templates/douyin/ 下的可用主题（目录含 default.yaml 即算一个）。"""
    themes = ["default"]
    base = root / "templates" / "douyin"
    if base.is_dir():
        for p in sorted(base.iterdir()):
            if p.is_dir() and (p / "default.yaml").is_file():
                themes.append(p.name)
    return themes


def _find_article(root: Path, name: str) -> Optional[Path]:
    for p in (root / "articles").glob("*/*.md"):
        if p.stem == name:
            return p
    return None


def _article_title(root: Path, name: str) -> str:
    p = _find_article(root, name)
    if p is None:
        return name
    try:
        doc, meta = parse(p.read_text(encoding="utf-8"))
        title = str(meta.get("title") or "").strip()
        if not title:
            for b in doc.children:
                if isinstance(b, Heading) and b.level == 1:
                    title = plain_text(b.children).strip()
                    break
        return title or name
    except Exception:
        return name


def _categories(root: Path) -> List[str]:
    arts_dir = root / "articles"
    if not arts_dir.is_dir():
        return []
    return sorted(d.name for d in arts_dir.iterdir() if d.is_dir())


def _not_found(env: Environment, name: str) -> HTMLResponse:
    return HTMLResponse(env.get_template("notfound.html.j2").render(name=name),
                        status_code=404)


def create_app(root: Path) -> FastAPI:
    root = Path(root)
    app = FastAPI(title="Knowledge Publisher Preview")
    env = Environment(
        loader=FileSystemLoader(str(root / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    out_dir = root / "output"
    out_dir.mkdir(exist_ok=True)
    app.mount("/output", StaticFiles(directory=str(out_dir)), name="output")
    static_dir = root / "templates" / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return env.get_template("index.html.j2").render(
            articles=_scan_articles(root),
            themes=_available_themes(root),
        )

    @app.get("/guide", response_class=HTMLResponse)
    def guide():
        return env.get_template("guide.html.j2").render()

    @app.get("/edit/{name}", response_class=HTMLResponse)
    def edit(name: str):
        article = _find_article(root, name)
        if article is None:
            return _not_found(env, name)
        content = article.read_text(encoding="utf-8")
        return env.get_template("edit.html.j2").render(
            article=name,
            title=_article_title(root, name),
            content=content,
            themes=_available_themes(root),
        )

    @app.post("/api/article/new")
    async def new_article(payload: dict):
        name = str(payload.get("name") or "").strip()
        category = str(payload.get("category") or "math").strip()
        if not _NAME_RE.match(name):
            return JSONResponse({"ok": False, "error": "文章名只能包含小写字母、数字和连字符（如 bayes）"}, status_code=400)
        if not _NAME_RE.match(category):
            return JSONResponse({"ok": False, "error": "分类名格式不正确"}, status_code=400)
        cat_dir = root / "articles" / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        target = cat_dir / f"{name}.md"
        if target.exists():
            return JSONResponse({"ok": False, "error": f"文章 {name} 已存在"}, status_code=409)
        title = name.replace("-", " ").replace("_", " ").title()
        content = (NEW_TEMPLATE
                   .replace("__TITLE__", title)
                   .replace("__SERIES__", "")
                   .replace("__AUTHOR__", ""))
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": f"/edit/{name}"}

    @app.post("/api/article/import")
    async def import_article(file: UploadFile = File(...),
                             category: str = Form("math")):
        """从浏览器上传 .md 文件导入系统。"""
        fname = (file.filename or "").strip()
        if not fname.lower().endswith((".md", ".markdown")):
            return JSONResponse({"ok": False, "error": "只支持 .md / .markdown 文件"}, status_code=400)
        content = (await file.read()).decode("utf-8", errors="replace")
        if not content.strip():
            return JSONResponse({"ok": False, "error": "文件内容为空"}, status_code=400)
        try:
            target = save_imported_article(root, Path(fname).stem, category, content)
        except ValueError as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
        return {"ok": True, "path": f"/edit/{target.stem}"}

    @app.post("/api/article/import-path")
    async def import_article_path(payload: dict):
        """从电脑上的本地路径导入 .md 文件（服务器与浏览器在同一台机器）。"""
        src = str(payload.get("path") or "").strip()
        category = str(payload.get("category") or "math").strip()
        p = Path(src)
        if not p.is_file():
            return JSONResponse({"ok": False, "error": f"找不到文件：{src}"}, status_code=404)
        if p.suffix.lower() not in (".md", ".markdown"):
            return JSONResponse({"ok": False, "error": "只支持 .md / .markdown 文件"}, status_code=400)
        content = p.read_text(encoding="utf-8", errors="replace")
        if not content.strip():
            return JSONResponse({"ok": False, "error": "文件内容为空"}, status_code=400)
        try:
            target = save_imported_article(root, p.stem, category, content)
        except ValueError as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
        return {"ok": True, "path": f"/edit/{target.stem}"}

    @app.post("/api/article/{name}")
    async def save_article(name: str, payload: dict):
        """保存文章内容，并重新生成知乎 + 抖音（默认主题）。"""
        article = _find_article(root, name)
        if article is None:
            return JSONResponse({"ok": False, "error": "文章不存在"}, status_code=404)
        content = str(payload.get("content") or "")
        if not content.strip():
            return JSONResponse({"ok": False, "error": "内容不能为空"}, status_code=400)
        try:
            article.write_text(content, encoding="utf-8")
            build_zhihu(article, root, out_dir)
            renderer = DouyinRenderer(root, out_dir)
            renderer.build(article)
            DouyinArticleRenderer(root, out_dir).build(article)
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"生成失败：{e}"}, status_code=500)
        return {"ok": True, "preview": f"/preview/{name}"}

    @app.delete("/api/article/{name}")
    async def delete_article(name: str):
        """删除文章母版与全部生成结果（不可恢复）。"""
        article = _find_article(root, name)
        if article is None:
            return JSONResponse({"ok": False, "error": "文章不存在"}, status_code=404)
        try:
            article.unlink()
            out_art = out_dir / name
            if out_art.exists():
                shutil.rmtree(out_art)
        except OSError as e:
            return JSONResponse({"ok": False, "error": f"删除失败：{e}"}, status_code=500)
        return {"ok": True}

    @app.get("/preview/{name}/douyin-article", response_class=HTMLResponse)
    def douyin_article(name: str):
        """抖音长文：公式已转图片的自包含 HTML，全选复制即可粘贴。"""
        article = _find_article(root, name)
        if article is None:
            return _not_found(env, name)
        html_path = DouyinArticleRenderer(root, out_dir).build_if_stale(article)
        return FileResponse(html_path, media_type="text/html")

    @app.get("/api/export/{name}/douyin-article.zip")
    def export_douyin_article_zip(name: str):
        """打包抖音长文：article.md + formulas/ 公式图片 + images/ 配图。"""
        article = _find_article(root, name)
        if article is None:
            return JSONResponse({"ok": False, "error": "文章不存在"}, status_code=404)
        art_dir = out_dir / name / "douyin-article"
        if not art_dir.is_dir():
            DouyinArticleRenderer(root, out_dir).build(article)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(art_dir.rglob("*")):
                if p.is_file():
                    z.write(p, arcname=f"{name}-douyin-article/{p.relative_to(art_dir)}")
        return Response(
            buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{name}-douyin-article.zip"'},
        )

    @app.get("/export/{name}", response_class=HTMLResponse)
    def export(name: str):
        """导出页：下载抖音图集 ZIP / 复制或下载知乎 Markdown。"""
        article = _find_article(root, name)
        if article is None:
            return _not_found(env, name)
        themes = _available_themes(root)
        douyin_dir = out_dir / name / "douyin"
        theme_pages = {}
        for t in themes:
            base = douyin_dir / t if t != "default" else douyin_dir
            if base.is_dir():
                theme_pages[t] = sorted(p.name for p in base.glob("*.png"))
        zhihu_md = out_dir / name / "zhihu" / "article.md"
        if not zhihu_md.exists():
            build_zhihu(article, root, out_dir)
        return env.get_template("export.html.j2").render(
            article=name,
            title=_article_title(root, name),
            themes=themes,
            theme_pages=theme_pages,
            image_dir_map={t: f"/output/{name}/douyin" + (f"/{t}" if t != "default" else "")
                           for t in themes},
        )

    @app.get("/api/export/{name}/douyin.zip")
    def export_douyin_zip(name: str, theme: str = "default"):
        """把某主题的全部抖音图集打包成 ZIP 下载。"""
        article = _find_article(root, name)
        if article is None:
            return JSONResponse({"ok": False, "error": "文章不存在"}, status_code=404)
        renderer = DouyinRenderer(root, out_dir, theme)
        renderer.build_if_stale(article)
        base = out_dir / name / "douyin"
        src = base if theme == "default" else base / theme
        if not src.is_dir():
            return JSONResponse({"ok": False, "error": "该主题尚未生成"}, status_code=404)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(src.glob("*.png")):
                z.write(p, arcname=f"{name}/{p.name}")
        return Response(
            buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{name}-douyin-{theme}.zip"'},
        )

    @app.get("/api/export/{name}/zhihu.md")
    def export_zhihu_md(name: str):
        article = _find_article(root, name)
        if article is None:
            return JSONResponse({"ok": False, "error": "文章不存在"}, status_code=404)
        zhihu_md = out_dir / name / "zhihu" / "article.md"
        if not zhihu_md.exists() or article.stat().st_mtime > zhihu_md.stat().st_mtime:
            build_zhihu(article, root, out_dir)
        return FileResponse(zhihu_md, media_type="text/markdown",
                            filename=f"{name}-zhihu.md")

    @app.get("/preview/{name}", response_class=HTMLResponse)
    def preview(name: str, theme: str = "default", embed: bool = False):
        article = _find_article(root, name)
        if article is None:
            return _not_found(env, name)
        themes = _available_themes(root)
        if theme not in themes:
            theme = "default"
        renderer = DouyinRenderer(root, out_dir, theme)
        renderer.build_if_stale(article)
        page_dir = renderer.output_page_dir(name)
        info_path = page_dir / "pages.json"
        info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {
            "title": name, "total": 0, "outline": []}
        image_dir = f"/output/{name}/douyin" + (f"/{theme}" if theme != "default" else "")
        return env.get_template("preview.html.j2").render(
            article=name,
            title=info.get("title", name),
            pages=info.get("total", 0),
            outline=info.get("outline", []),
            pages_kinds=[p.get("kind", "") for p in info.get("pages", [])],
            theme=theme,
            themes=themes,
            image_dir=image_dir,
            embed=embed,
        )

    @app.get("/preview/{name}/zhihu", response_class=HTMLResponse)
    def zhihu(name: str):
        article = _find_article(root, name)
        if article is None:
            return HTMLResponse("<p>not found</p>", status_code=404)
        out_zhihu = out_dir / name / "zhihu" / "article.html"
        if not out_zhihu.exists() or article.stat().st_mtime > out_zhihu.stat().st_mtime:
            build_zhihu(article, root, out_dir)
        return FileResponse(out_zhihu)

    return app


def run_preview(root: Path, name: Optional[str], port: int, theme: str = "default",
                open_browser: bool = True) -> None:
    import uvicorn

    app = create_app(root)
    url = (f"http://127.0.0.1:{port}/" if not name
           else f"http://127.0.0.1:{port}/preview/{name}?theme={theme}")
    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
