"""抖音长文渲染器：公式 → PNG 图片，输出可直接粘贴到抖音文章编辑器的内容。

抖音文章编辑器不支持 LaTeX 渲染，因此系统把每个公式渲染成 PNG 图片：

- article.html —— 完全自包含（图片 base64 内嵌），浏览器里全选复制，
  粘贴到抖音文章编辑器时文字与公式图片一起带过去，这是推荐路径。
- article.md   —— 公式以 ![公式N](formulas/fNN.png) 引用，
  可配合 formulas/ 目录在编辑器中手动插入图片。

输出目录：output/<文章>/douyin-article/
"""
from __future__ import annotations

import base64
import html
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..assets import resolve_asset
from ..ast_nodes import (
    BlockQuote, CodeBlock, Document, Emphasis, Heading, HR, Image as ImageNode,
    InlineCode, Link, ListBlock, MathBlock, MathInline, Node, Paragraph,
    Strong, Table, Text, plain_text, walk,
)
from ..parser import parse
from .latex import LatexRenderer

STYLE = """
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;max-width:720px;margin:0 auto;padding:32px 24px 80px;line-height:1.9;color:#26272b;background:#fff}
h1{font-size:1.9em;margin:0 0 .4em}
h2{font-size:1.45em;margin:2em 0 .6em;border-left:4px solid #1667d9;padding-left:12px}
h3{font-size:1.2em;margin:1.6em 0 .4em}
p{margin:1em 0}
blockquote{margin:1.2em 0;padding:12px 18px;background:#f7f8fa;border-left:4px solid #1667d9;color:#475467}
pre{background:#f6f8fa;padding:16px 18px;border-radius:8px;overflow:auto;font-size:.92em;line-height:1.55;font-family:Consolas,Menlo,monospace}
p code,li code{background:#eef1f5;padding:2px 6px;border-radius:4px;font-size:.9em;font-family:Consolas,Menlo,monospace}
table{border-collapse:collapse;width:100%;margin:1.4em 0}
th,td{border:1px solid #e5e7eb;padding:10px 14px;text-align:left}
th{background:#1667d9;color:#fff}
tr:nth-child(even) td{background:#fafbfc}
img{max-width:100%}
hr{border:none;border-top:1px solid #e5e7eb;margin:2.4em 0}
.f-block{text-align:center;margin:1.6em 0}
.f-block img{max-width:100%}
.f-inline{height:1.3em;vertical-align:middle}
"""


class DouyinArticleRenderer:
    def __init__(self, project_root: Path, output_root: Path):
        self.root = Path(project_root)
        self.output_root = Path(output_root)
        self.latex = LatexRenderer()

    # ---------- 公式 ----------

    def _formula_assets(self, latex: str, formulas_dir: Path, n: int,
                        inline: bool) -> Tuple[Optional[str], Optional[str]]:
        """返回 (图片文件相对路径, base64 data uri)。"""
        img, err = self.latex.render(latex)
        if img is None:
            return None, None
        fname = f"f{n:02d}.png"
        img.save(formulas_dir / fname)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"formulas/{fname}", f"data:image/png;base64,{b64}"

    # ---------- 行内 ----------

    def _inline(self, children: List[Node], formula_index: Dict[int, int],
                formulas_dir: Path, images_dir: Path, article_dir: Path,
                mode: str) -> Tuple[str, str]:
        md_parts, html_parts = [], []
        for node in children:
            if isinstance(node, Text):
                md_parts.append(node.text)
                html_parts.append(html.escape(node.text))
            elif isinstance(node, Strong):
                m, h = self._inline(node.children, formula_index, formulas_dir,
                                    images_dir, article_dir, mode)
                md_parts.append(f"**{m}**")
                html_parts.append(f"<strong>{h}</strong>")
            elif isinstance(node, Emphasis):
                m, h = self._inline(node.children, formula_index, formulas_dir,
                                    images_dir, article_dir, mode)
                md_parts.append(f"*{m}*")
                html_parts.append(f"<em>{h}</em>")
            elif isinstance(node, InlineCode):
                md_parts.append(f"`{node.text}`")
                html_parts.append(f"<code>{html.escape(node.text)}</code>")
            elif isinstance(node, Link):
                m, h = self._inline(node.children, formula_index, formulas_dir,
                                    images_dir, article_dir, mode)
                md_parts.append(f"[{m}]({node.href})")
                html_parts.append(f'<a href="{html.escape(node.href, quote=True)}">{h}</a>')
            elif isinstance(node, MathInline):
                n = formula_index[id(node)]
                rel, b64 = self._formula_assets(node.latex, formulas_dir, n, inline=True)
                if rel:
                    md_parts.append(f"![公式{n}]({rel})")
                    html_parts.append(f'<img class="f-inline" src="{b64}" alt="公式{n}">')
            elif isinstance(node, ImageNode):
                m, h = self._image(node, images_dir, article_dir)
                md_parts.append(m)
                html_parts.append(h)
        return "".join(md_parts), "".join(html_parts)

    def _image(self, node: ImageNode, images_dir: Path, article_dir: Path) -> Tuple[str, str]:
        src = node.src
        md = f"![{node.alt}]({src})"
        p = resolve_asset(self.root, article_dir, src)
        if p is None or p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            return md, f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(node.alt)}">'
        target = images_dir / p.name
        if not target.exists():
            target.write_bytes(p.read_bytes())
        with open(target, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = "png" if p.suffix.lower() == ".png" else "jpeg"
        md = f"![{node.alt}](images/{p.name})"
        h = f'<img src="data:image/{ext};base64,{b64}" alt="{html.escape(node.alt)}">'
        return md, h

    # ---------- 块级 ----------

    def _block(self, block: Node, formulas_dir: Path, images_dir: Path,
               formula_index: Dict[int, int], article_dir: Path) -> Tuple[str, str]:
        if isinstance(block, Heading):
            m, h = self._inline(block.children, formula_index, formulas_dir,
                                images_dir, article_dir, "md")
            return "#" * block.level + " " + m, f"<h{block.level}>{h}</h{block.level}>"
        if isinstance(block, Paragraph):
            return self._inline(block.children, formula_index, formulas_dir,
                                images_dir, article_dir, "md")
        if isinstance(block, MathBlock):
            n = formula_index[id(block)]
            rel, b64 = self._formula_assets(block.latex, formulas_dir, n, inline=False)
            if rel:
                return f"![公式{n}]({rel})", f'<div class="f-block"><img src="{b64}" alt="公式{n}"></div>'
            return "", ""
        if isinstance(block, CodeBlock):
            m, h = block.content, html.escape(block.content)
            return f"```{block.language}\n{m}\n```", f"<pre><code>{h}</code></pre>"
        if isinstance(block, ListBlock):
            md_lines, html_items = [], []
            for i, item in enumerate(block.items):
                texts = [c for c in item.children if isinstance(c, Paragraph)]
                m, h = self._inline(texts[0].children if texts else [], formula_index,
                                    formulas_dir, images_dir, article_dir, "md")
                bullet = f"{block.start + i}." if block.ordered else "-"
                md_lines.append(f"{bullet} {m}")
                tag = "ol" if block.ordered else "ul"
                html_items.append(f"<li>{h}</li>")
            return "\n".join(md_lines), f"<{tag}>{''.join(html_items)}</{tag}>"
        if isinstance(block, BlockQuote):
            inner = "\n".join(self._block(c, formulas_dir, images_dir, formula_index,
                                          article_dir)[0]
                              for c in block.children if isinstance(c, Paragraph))
            return "> " + inner.replace("\n", "\n> "), f"<blockquote>{inner}</blockquote>"
        if isinstance(block, Table):
            md_rows = ["| " + " | ".join(self._inline(c, formula_index, formulas_dir,
                                                      images_dir, article_dir, "md")[0]
                                         for c in block.headers) + " |"]
            md_rows.append("| " + " | ".join("---" for _ in block.headers) + " |")
            for row in block.rows:
                md_rows.append("| " + " | ".join(
                    self._inline(c, formula_index, formulas_dir, images_dir,
                                 article_dir, "md")[0].replace("|", "\\|") for c in row) + " |")
            thead = "".join(f"<th>{self._inline(c, formula_index, formulas_dir, images_dir, article_dir, 'html')[1]}</th>" for c in block.headers)
            rows = "".join(
                "<tr>" + "".join(
                    f"<td>{self._inline(c, formula_index, formulas_dir, images_dir, article_dir, 'html')[1]}</td>"
                    for c in row) + "</tr>" for row in block.rows)
            return "\n".join(md_rows), f"<table><thead><tr>{thead}</tr></thead><tbody>{rows}</tbody></table>"
        if isinstance(block, ImageNode):
            return self._image(block, images_dir, article_dir)
        if isinstance(block, HR):
            return "---", "<hr>"
        return "", ""

    # ---------- 构建入口 ----------

    def build(self, article_path: Path) -> Dict[str, Path]:
        article_path = Path(article_path)
        text = article_path.read_text(encoding="utf-8")
        doc, meta = parse(text)

        out_dir = self.output_root / article_path.stem / "douyin-article"
        formulas_dir = out_dir / "formulas"
        images_dir = out_dir / "images"
        formulas_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(exist_ok=True)

        # 文档顺序编号所有公式
        formula_index: Dict[int, int] = {}
        n = 0
        for node in walk(doc):
            if isinstance(node, (MathBlock, MathInline)):
                n += 1
                formula_index[id(node)] = n

        md_parts, html_parts = [], []
        for block in doc.children:
            m, h = self._block(block, formulas_dir, images_dir, formula_index,
                               article_path.parent)
            md_parts.append(m)
            html_parts.append(h)

        title = str(meta.get("title") or "").strip()
        if not title:
            for b in doc.children:
                if isinstance(b, Heading) and b.level == 1:
                    title = plain_text(b.children).strip()
                    break
        author = str(meta.get("author") or "").strip()
        series = str(meta.get("series") or "").strip()

        md_path = out_dir / "article.md"
        md_path.write_text("\n\n".join(p for p in md_parts if p) + "\n", encoding="utf-8")

        html_text = (
            "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            f"<title>{html.escape(title or '未命名文章')}</title>\n"
            f"<style>{STYLE}</style>\n</head>\n<body>\n"
            + (f"<p style=\"color:#1667d9;font-weight:600\">{html.escape(series)}</p>\n" if series else "")
            + f"<h1>{html.escape(title or '未命名文章')}</h1>\n"
            + (f"<p style=\"color:#98a2b3\">@{html.escape(author)}</p>\n" if author else "")
            + "".join(h for h in html_parts if h)
            + "\n</body>\n</html>\n"
        )
        html_path = out_dir / "article.html"
        html_path.write_text(html_text, encoding="utf-8")

        return {"md": md_path, "html": html_path,
                "formulas": formulas_dir, "images": images_dir}

    def build_if_stale(self, article_path: Path) -> Path:
        out_dir = self.output_root / article_path.stem / "douyin-article"
        marker = out_dir / "article.html"
        if marker.exists() and article_path.stat().st_mtime <= marker.stat().st_mtime:
            return marker
        return self.build(article_path)["html"]
