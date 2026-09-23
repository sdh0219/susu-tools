"""Markdown 母版 → AST 解析器。

母版规范（V1.0）：
- 支持元素：标题 / 段落 / 粗体 / 斜体 / 列表 / 引用 / 代码 / 公式 / 图片 / 表格 / 分割线 / 链接
- 公式统一只允许 `$$...$$` 块公式 + `$...$` 行内公式
- 可选 YAML frontmatter（title / subtitle / series / author / tags）
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin

from .ast_nodes import (
    BlockQuote, CodeBlock, Document, Emphasis, Heading, HR, Image, InlineCode,
    Link, ListBlock, ListItem, MathBlock, MathInline, Node, Paragraph, Strong,
    Table, Text,
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)

_MD: Optional[MarkdownIt] = None


def build_md() -> MarkdownIt:
    global _MD
    if _MD is None:
        _MD = MarkdownIt("gfm-like", {"html": True, "linkify": False}).use(
            texmath_plugin, delimiters="dollars"
        )
    return _MD


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[m.end():]


def parse(text: str) -> Tuple[Document, dict]:
    """解析母版，返回 (Document AST, frontmatter meta)。"""
    meta, body = parse_frontmatter(text)
    tokens = build_md().parse(body)
    children, _ = _parse_blocks(tokens, 0, len(tokens))
    return Document(children=children), meta


# ---------- 行内解析 ----------

def _parse_inline_children(inline_token) -> List[Node]:
    """markdown-it 把行内内容放在 inline token 的 children 中，这里解析它。"""
    if inline_token.type == "inline":
        kids, _ = _parse_inline(inline_token.children, 0, len(inline_token.children))
        return kids
    return []


def _parse_inline(tokens, i: int, end: int) -> Tuple[List[Node], int]:
    nodes: List[Node] = []
    while i < end:
        t = tokens[i]
        if t.type == "text":
            nodes.append(Text(text=t.content))
            i += 1
        elif t.type == "softbreak":
            nodes.append(Text(text=" "))
            i += 1
        elif t.type == "hardbreak":
            nodes.append(Text(text=" "))
            i += 1
        elif t.type == "math_inline":
            nodes.append(MathInline(latex=t.content))
            i += 1
        elif t.type == "math":
            if t.meta and t.meta.get("type") == "block":
                nodes.append(MathBlock(latex=t.content))
            else:
                nodes.append(MathInline(latex=t.content))
            i += 1
        elif t.type == "code_inline":
            nodes.append(InlineCode(text=t.content))
            i += 1
        elif t.type == "image":
            attrs = dict(t.attrs or [])
            nodes.append(Image(src=attrs.get("src", ""), alt=t.content))
            i += 1
        elif t.type == "strong_open":
            kids, i = _parse_inline(tokens, i + 1, end)
            nodes.append(Strong(children=kids))
        elif t.type == "em_open":
            kids, i = _parse_inline(tokens, i + 1, end)
            nodes.append(Emphasis(children=kids))
        elif t.type == "link_open":
            attrs = dict(t.attrs or [])
            kids, i = _parse_inline(tokens, i + 1, end)
            nodes.append(Link(href=attrs.get("href", ""), children=kids))
        elif t.type in ("strong_close", "em_close", "link_close"):
            return nodes, i + 1
        elif t.type.endswith("_open"):
            # 未知行内开标签（如删除线 s_open）：保留内容，去掉样式
            kids, i = _parse_inline(tokens, i + 1, end)
            nodes.extend(kids)
        else:
            i += 1
    return nodes, i


# ---------- 块级解析 ----------

def _parse_blocks(tokens, i: int, end: int) -> Tuple[List[Node], int]:
    nodes: List[Node] = []
    while i < end:
        t = tokens[i]
        if t.type in ("list_item_close", "bullet_list_close", "ordered_list_close",
                      "blockquote_close", "table_close"):
            # 容器闭合：交还给调用方处理
            return nodes, i
        if t.type == "heading_open":
            level = int(t.tag[1])
            kids = _parse_inline_children(tokens[i + 1])
            i += 2
            if i < end and tokens[i].type == "heading_close":
                i += 1
            nodes.append(Heading(level=level, children=kids))
        elif t.type == "paragraph_open":
            kids = _parse_inline_children(tokens[i + 1])
            i += 2
            if i < end and tokens[i].type == "paragraph_close":
                i += 1
            if len(kids) == 1 and isinstance(kids[0], Image):
                # 单独成段的图片提升为块级节点，便于分页与整图渲染
                nodes.append(kids[0])
            else:
                nodes.append(Paragraph(children=kids))
        elif t.type == "math_block":
            nodes.append(MathBlock(latex=t.content))
            i += 1
        elif t.type == "math":
            nodes.append(MathBlock(latex=t.content))
            i += 1
        elif t.type == "fence":
            info = (t.info or "").strip().split()
            nodes.append(CodeBlock(language=info[0] if info else "", content=t.content))
            i += 1
        elif t.type == "hr":
            nodes.append(HR())
            i += 1
        elif t.type == "blockquote_open":
            kids, i = _parse_blocks(tokens, i + 1, end)
            if i < end and tokens[i].type == "blockquote_close":
                i += 1
            nodes.append(BlockQuote(children=kids))
        elif t.type in ("bullet_list_open", "ordered_list_open"):
            ordered = t.type == "ordered_list_open"
            start = 1
            for k, v in (t.attrs or []):
                if k == "start":
                    try:
                        start = int(v)
                    except (TypeError, ValueError):
                        start = 1
            i += 1
            items: List[ListItem] = []
            while i < end and tokens[i].type != (
                "ordered_list_close" if ordered else "bullet_list_close"
            ):
                if tokens[i].type == "list_item_open":
                    kids, i = _parse_blocks(tokens, i + 1, end)
                    if i < end and tokens[i].type == "list_item_close":
                        i += 1
                    items.append(ListItem(children=kids))
                else:
                    i += 1
            if i < end:
                i += 1
            nodes.append(ListBlock(ordered=ordered, start=start, items=items))
        elif t.type == "table_open":
            table, i = _parse_table(tokens, i)
            nodes.append(table)
        else:
            i += 1
    return nodes, i


def _parse_table(tokens, i: int) -> Tuple[Table, int]:
    """解析 GFM 表格；i 指向 table_open。"""
    headers: List[List[Node]] = []
    rows: List[List[List[Node]]] = []
    i += 1
    in_thead = False
    cur_row: List[List[Node]] | None = None
    while i < len(tokens) and tokens[i].type != "table_close":
        t = tokens[i]
        if t.type == "thead_open":
            in_thead = True
        elif t.type == "tbody_open":
            in_thead = False
        elif t.type == "tr_open":
            cur_row = []
        elif t.type == "tr_close":
            if cur_row is not None:
                if in_thead:
                    headers = cur_row
                else:
                    rows.append(cur_row)
            cur_row = None
        elif t.type == "inline":
            kids = _parse_inline_children(tokens[i])
            if cur_row is not None:
                cur_row.append(kids)
        i += 1
    return Table(headers=headers, rows=rows), i + 1
