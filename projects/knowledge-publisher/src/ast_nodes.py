"""AST 中间层：Markdown 母版解析后的统一数据结构。

所有平台渲染器（知乎 / 抖音 / 未来扩展）只依赖这一层，
不直接接触 Markdown 文本，保证「一次创作，多平台输出」。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Node:
    """所有节点的基类"""


# ---------- 行内节点 ----------

@dataclass
class Text(Node):
    text: str


@dataclass
class Strong(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class Emphasis(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class InlineCode(Node):
    text: str


@dataclass
class Link(Node):
    href: str
    children: List[Node] = field(default_factory=list)


@dataclass
class Image(Node):
    src: str
    alt: str = ""


@dataclass
class MathInline(Node):
    latex: str


# ---------- 块级节点 ----------

@dataclass
class Paragraph(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class Heading(Node):
    level: int
    children: List[Node] = field(default_factory=list)


@dataclass
class MathBlock(Node):
    latex: str


@dataclass
class CodeBlock(Node):
    language: str
    content: str


@dataclass
class ListItem(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class ListBlock(Node):
    ordered: bool
    start: int = 1
    items: List[ListItem] = field(default_factory=list)


@dataclass
class BlockQuote(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class Table(Node):
    headers: List[List[Node]] = field(default_factory=list)
    rows: List[List[List[Node]]] = field(default_factory=list)


@dataclass
class HR(Node):
    pass


@dataclass
class Document(Node):
    children: List[Node] = field(default_factory=list)


def walk(node: Node):
    """深度优先遍历所有节点（含自身）。"""
    yield node
    if isinstance(node, ListBlock):
        for item in node.items:
            yield from walk(item)
        return
    if isinstance(node, Table):
        for row in [node.headers, *node.rows]:
            for cell in row:
                for n in cell:
                    yield from walk(n)
        return
    for child in getattr(node, "children", []):
        yield from walk(child)


def plain_text(nodes: List[Node]) -> str:
    """取一组行内节点的纯文本（公式以 $..$ 表示）。"""
    parts = []
    for n in nodes:
        if isinstance(n, Text):
            parts.append(n.text)
        elif isinstance(n, InlineCode):
            parts.append(n.text)
        elif isinstance(n, MathInline):
            parts.append(f"${n.latex}$")
        elif isinstance(n, Image):
            parts.append(n.alt or n.src)
        elif isinstance(n, Link):
            parts.append(plain_text(n.children))
        else:
            parts.append(plain_text(getattr(n, "children", [])))
    return "".join(parts)
