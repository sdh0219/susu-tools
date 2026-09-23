"""知乎渲染器：Markdown 母版 → 知乎发布包。

输出 output/<文章>/zhihu/：
- article.md    干净的 Markdown（公式保留 $..$ / $$..$$，知乎可直接粘贴）
- article.html  带样式与 MathJax 的完整 HTML（本地预览用）
- assets/       引用的图片（自动复制并改写引用路径）
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

from ..assets import resolve_asset
from ..ast_nodes import (
    BlockQuote, CodeBlock, Document, Emphasis, Heading, HR, Image as ImageNode,
    InlineCode, Link, ListBlock, MathBlock, MathInline, Node, Paragraph,
    Strong, Table, Text, plain_text, walk,
)
from ..parser import parse

BLOCK_TYPES = (Heading, Paragraph, MathBlock, CodeBlock, ListBlock, BlockQuote,
               Table, ImageNode, HR)


def inline_md(children, src_map: Optional[Dict[str, str]] = None) -> str:
    parts = []
    for n in children:
        if isinstance(n, Text):
            parts.append(n.text)
        elif isinstance(n, Strong):
            parts.append(f"**{inline_md(n.children, src_map)}**")
        elif isinstance(n, Emphasis):
            parts.append(f"*{inline_md(n.children, src_map)}*")
        elif isinstance(n, InlineCode):
            parts.append(f"`{n.text}`")
        elif isinstance(n, Link):
            parts.append(f"[{inline_md(n.children, src_map)}]({n.href})")
        elif isinstance(n, MathInline):
            parts.append(f"${n.latex}$")
        elif isinstance(n, ImageNode):
            src = src_map.get(n.src, n.src) if src_map else n.src
            parts.append(f"![{n.alt}]({src})")
        else:
            parts.append("")
    return "".join(parts)


def _cell_md(cells) -> str:
    return " | ".join(inline_md(c).replace("|", "\\|") for c in cells)


def _block_md(block, src_map=None) -> str:
    if isinstance(block, Heading):
        return "#" * block.level + " " + inline_md(block.children, src_map)
    if isinstance(block, Paragraph):
        return inline_md(block.children, src_map)
    if isinstance(block, MathBlock):
        return "$$\n" + block.latex.strip() + "\n$$"
    if isinstance(block, CodeBlock):
        return f"```{block.language}\n{block.content}\n```"
    if isinstance(block, ListBlock):
        lines = []
        for i, item in enumerate(block.items):
            text = _item_md(item, src_map)
            bullet = f"{block.start + i}." if block.ordered else "-"
            lines.append(f"{bullet} {text}")
        return "\n".join(lines)
    if isinstance(block, BlockQuote):
        inner = "\n".join(_block_md(c, src_map) for c in block.children)
        return "\n".join("> " + ln for ln in inner.splitlines())
    if isinstance(block, Table):
        lines = ["| " + _cell_md(block.headers) + " |"]
        lines.append("| " + " | ".join("---" for _ in block.headers) + " |")
        for row in block.rows:
            lines.append("| " + _cell_md(row) + " |")
        return "\n".join(lines)
    if isinstance(block, ImageNode):
        src = src_map.get(block.src, block.src) if src_map else block.src
        return f"![{block.alt}]({src})"
    if isinstance(block, HR):
        return "---"
    return ""


def _item_md(item, src_map=None) -> str:
    parts = []
    for child in item.children:
        if isinstance(child, Paragraph):
            parts.append(inline_md(child.children, src_map))
        elif isinstance(child, ListBlock):
            sub = _block_md(child, src_map)
            parts.append("\n" + "\n".join("  " + ln for ln in sub.splitlines()))
        else:
            parts.append(_block_md(child, src_map))
    return " ".join(parts)


def to_markdown(doc: Document, src_map: Optional[Dict[str, str]] = None) -> str:
    return "\n\n".join(_block_md(b, src_map) for b in doc.children if isinstance(b, BLOCK_TYPES))


def _code_html(lang: str, content: str) -> str:
    lexer = get_lexer_by_name(lang) if lang else TextLexer()
    code = highlight(content, lexer, HtmlFormatter(style="friendly", nowrap=True))
    return f'<pre class="highlight"><code>{code}</code></pre>'


def to_html(doc: Document, meta: dict, project_root: Path,
            src_map: Optional[Dict[str, str]] = None) -> str:
    parts = []
    for block in doc.children:
        if isinstance(block, CodeBlock):
            parts.append(_code_html(block.language, block.content))
        elif isinstance(block, BLOCK_TYPES):
            parts.append(_block_md(block, src_map))
    md = MarkdownIt("gfm-like", {"html": True, "linkify": False})
    content = md.render("\n\n".join(parts))
    title = str(meta.get("title") or "").strip()
    if not title:
        for b in doc.children:
            if isinstance(b, Heading) and b.level == 1:
                title = plain_text(b.children).strip()
                break
    env = Environment(
        loader=FileSystemLoader(str(project_root / "templates" / "zhihu")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("article.html.j2")
    return tpl.render(
        title=title or "未命名文章",
        author=meta.get("author", ""),
        series=meta.get("series", ""),
        content=content,
        highlight_css=HtmlFormatter(style="friendly").get_style_defs(".highlight"),
    )


def build(article_path: Path, project_root: Path, output_root: Path) -> Dict[str, Path]:
    article_path = Path(article_path)
    text = article_path.read_text(encoding="utf-8")
    doc, meta = parse(text)

    # 复制图片并改写引用
    src_map: Dict[str, str] = {}
    out_dir = output_root / article_path.stem / "zhihu"
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for node in walk(doc):
        if isinstance(node, ImageNode):
            p = resolve_asset(project_root, article_path.parent, node.src)
            if p and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                target = assets_dir / p.name
                if not target.exists():
                    target.write_bytes(p.read_bytes())
                src_map[node.src] = f"assets/{p.name}"

    md_text = to_markdown(doc, src_map)
    html_text = to_html(doc, meta, project_root, src_map)
    md_path = out_dir / "article.md"
    html_path = out_dir / "article.html"
    md_path.write_text(md_text + "\n", encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    return {"md": md_path, "html": html_path, "assets": assets_dir}
