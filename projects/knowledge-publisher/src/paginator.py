"""抖音分页器：按「内容块 / 视觉单元」分页，而不是按字数分页。

规则：
- 第 1 页为封面，最后一页为结尾卡片
- 每个 h2/h3 知识点尽量独立成页
- 公式与紧邻的短引导段落保持同页
- 超长代码 / 表格 / 段落按行切分，跨页续接
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .ast_nodes import (
    CodeBlock, Document, Heading, ListBlock, MathBlock, Node, Paragraph,
    Table, Text, plain_text,
)


@dataclass
class CodeChunk:
    """跨页续接的代码片段。"""
    language: str
    lines: List[str]
    index: int = 1
    total: int = 1


@dataclass
class Page:
    kind: str                        # cover | content | summary
    blocks: List[object] = field(default_factory=list)
    used: float = 0.0                # 已占用高度（由渲染器测量提供）
    index: int = 0
    outline: Optional[str] = None    # 本页起始的标题（用于预览大纲）


def paginate(doc: Document, meta: dict, renderer) -> Tuple[List[Page], List[dict]]:
    """返回 (pages, outline)。outline: [{title, page}]，供预览器大纲使用。"""
    cfg = renderer.cfg("default")
    canvas_h = int(cfg["canvas"]["height"])
    pad = cfg["padding"]
    footer_h = 70
    content_h = canvas_h - int(pad["top"]) - int(pad["bottom"]) - footer_h

    pages: List[Page] = [Page(kind="cover")]
    cur: Optional[Page] = None
    outline: List[dict] = []

    def new_page() -> Page:
        nonlocal cur
        cur = Page(kind="content")
        pages.append(cur)
        return cur

    def fits(h: float, page: Optional[Page]) -> bool:
        return page is None or page.used + h <= content_h

    def place(page: Page, block, h: float) -> None:
        page.blocks.append(block)
        page.used += h

    blocks = [b for b in doc.children if not (isinstance(b, Heading) and b.level == 1)]
    if not blocks:
        return pages, outline

    cur = new_page()

    for block in blocks:
        if isinstance(block, Heading):
            if cur.blocks:
                cur = new_page()
            text = plain_text(block.children).strip()
            if text:
                cur.outline = text
                outline.append({"title": text, "page": cur})
            place(cur, block, renderer.measure_heading(block))
        elif isinstance(block, MathBlock):
            h = renderer.measure_math(block)
            if cur.blocks and not fits(h, cur):
                if _pull_label(pages, cur, block, h, renderer, content_h):
                    continue
                cur = new_page()
            place(cur, block, h)
        elif isinstance(block, CodeBlock):
            cur = _place_code(renderer, cur, block, content_h, new_page, place)
        elif isinstance(block, Table):
            cur = _place_table(renderer, cur, block, content_h, new_page, place)
        elif isinstance(block, Paragraph):
            cur = _place_paragraph(renderer, cur, block, content_h, new_page, place)
        else:
            h = renderer.measure_block(block)
            if cur.blocks and not fits(h, cur):
                cur = new_page()
            place(cur, block, h)

    # 结尾卡片
    pages.append(Page(kind="summary"))

    # 编号 + 大纲页码回填
    for i, p in enumerate(pages):
        p.index = i + 1
    for item in outline:
        if isinstance(item["page"], Page):
            item["page"] = item["page"].index
        else:
            item["page"] = 1
    return pages, outline


def _pull_label(pages, cur: Page, math_block: MathBlock, math_h: float,
                renderer, content_h: float) -> bool:
    """公式放不下时，把上一页末尾的短引导段落拉到新页，与公式同页展示。"""
    if not cur.blocks:
        return False
    last = cur.blocks[-1]
    if not isinstance(last, Paragraph):
        return False
    text = plain_text(last.children)
    if len(text) > 80:
        return False
    para_h = renderer.measure_block(last)
    gap = float(renderer.cfg("default").get("spacing", {}).get("block_gap", 22))
    if para_h + math_h + gap > content_h:
        return False
    cur.blocks.pop()
    cur.used -= para_h
    nxt = Page(kind="content", outline=cur.outline)
    pages.append(nxt)
    nxt.blocks.append(last)
    nxt.used += para_h
    nxt.blocks.append(math_block)
    nxt.used += math_h + gap
    return True


def _place_code(renderer, cur, block: CodeBlock, content_h: float,
                new_page, place) -> Page:
    lines = block.content.split("\n")
    total = len(lines)
    while True:
        if cur.blocks and not renderer.fits_page(cur, renderer.measure_code(block), content_h):
            cur = new_page()
        if not renderer.measure_code(block) <= content_h:
            max_lines = renderer.max_code_lines(content_h)
            max_lines = max(1, max_lines)
            n_chunks = (total + max_lines - 1) // max_lines
            for ci in range(n_chunks):
                chunk_lines = lines[ci * max_lines:(ci + 1) * max_lines]
                if not chunk_lines:
                    continue
                chunk = CodeChunk(language=block.language, lines=chunk_lines,
                                  index=ci + 1, total=n_chunks)
                if cur.blocks and not renderer.fits_page(cur, renderer.measure_code_chunk(chunk), content_h):
                    cur = new_page()
                place(cur, chunk, renderer.measure_code_chunk(chunk))
            return cur
        place(cur, block, renderer.measure_code(block))
        return cur


def _place_table(renderer, cur, block: Table, content_h: float,
                 new_page, place) -> Page:
    full_h = renderer.measure_table(block)
    if full_h <= content_h:
        if cur.blocks and not renderer.fits_page(cur, full_h, content_h):
            cur = new_page()
        place(cur, block, full_h)
        return cur
    # 按行切分跨页（表头每页重复）
    max_rows = renderer.max_table_rows(content_h)
    max_rows = max(1, max_rows)
    rows = list(block.rows)
    for i in range(0, len(rows), max_rows):
        chunk = Table(headers=block.headers, rows=rows[i:i + max_rows])
        h = renderer.measure_table(chunk)
        if cur.blocks and not renderer.fits_page(cur, h, content_h):
            cur = new_page()
        place(cur, chunk, h)
    return cur


def _place_paragraph(renderer, cur, block: Paragraph, content_h: float,
                     new_page, place) -> Page:
    h = renderer.measure_block(block)
    if h <= content_h:
        if cur.blocks and not renderer.fits_page(cur, h, content_h):
            cur = new_page()
        place(cur, block, h)
        return cur
    # 超长段落：按行内子节点切分为多个短段落
    groups: List[List[Node]] = []
    cur_group: List[Node] = []
    cur_h = 0.0
    for child in block.children:
        ch = renderer.measure_inline_height(child)
        if cur_group and cur_h + ch > content_h:
            groups.append(cur_group)
            cur_group = []
            cur_h = 0.0
        cur_group.append(child)
        cur_h += ch
    if cur_group:
        groups.append(cur_group)
    if not groups:
        groups = [block.children]
    for g in groups:
        sub = Paragraph(children=g)
        h = renderer.measure_block(sub)
        if cur.blocks and not renderer.fits_page(cur, h, content_h):
            cur = new_page()
        place(cur, sub, h)
    return cur
