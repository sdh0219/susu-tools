"""内容检查器：kp check 的核心。

检查项：
- Markdown 是否合法（frontmatter / 代码块闭合）
- LaTeX 公式能否渲染（matplotlib mathtext 实测）
- 图片是否存在、是否损坏
- 标题层级是否正确、是否存在空标题
- 是否存在超长段落 / 文字密度过高的知识点
- 代码块语言是否可高亮、表格列数是否超限
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PIL import Image, UnidentifiedImageError

from .assets import resolve_asset
from .ast_nodes import (
    BlockQuote, CodeBlock, Document, Heading, Image as ImageNode, ListBlock,
    MathBlock, MathInline, Node, Paragraph, Table, Text, plain_text, walk,
)
from .parser import parse

_FENCE_RE = re.compile(r"^\s*```")


def latex_syntax_check(latex: str) -> Optional[str]:
    """轻量 LaTeX 语法检查（面向 V1 支持的 mathtext 子集）。

    检查：花括号配对、\\begin/\\end 环境配对、上下标后必须有内容。
    """
    if latex.count("{") != latex.count("}"):
        return (f"花括号不配对（{latex.count('{')} 个 '{{'，"
                f"{latex.count('}')} 个 '}}'）")
    stack = []
    for m in re.finditer(r"\\(begin|end)\{([^}]*)\}", latex):
        if m.group(1) == "begin":
            stack.append(m.group(2))
        else:
            if not stack or stack.pop() != m.group(2):
                return f"环境 \\end{{{m.group(2)}}} 与 \\begin 不匹配"
    if stack:
        return f"环境 \\begin{{{stack[-1]}}} 未闭合"
    if re.search(r"[\^_](?=$|[\^_])", latex):
        return "上/下标符号（^/_）后缺少内容"
    return None


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def check_article(article_path: Path, project_root: Path, config: dict) -> Report:
    report = Report()
    try:
        text = article_path.read_text(encoding="utf-8")
    except OSError as e:
        report.errors.append(f"无法读取文件：{e}")
        return report

    doc, meta = parse(text)
    limits = config.get("content", {})
    max_para = limits.get("max_paragraph_chars", 350)
    max_section = limits.get("max_section_chars", 950)
    max_cols = limits.get("max_table_columns", 6)

    # ---- 基础统计 ----
    stats = {"formulas": 0, "images": 0, "code_blocks": 0, "tables": 0}
    formula_list: List[MathBlock | MathInline] = []
    image_list: List[ImageNode] = []
    for node in walk(doc):
        if isinstance(node, (MathBlock, MathInline)):
            stats["formulas"] += 1
            formula_list.append(node)
        elif isinstance(node, ImageNode):
            stats["images"] += 1
            image_list.append(node)
        elif isinstance(node, CodeBlock):
            stats["code_blocks"] += 1
        elif isinstance(node, Table):
            stats["tables"] += 1

    # ---- Markdown 合法性 ----
    fences = [n for n in text.splitlines() if _FENCE_RE.match(n)]
    if len(fences) % 2 == 1:
        report.errors.append("代码块未闭合：``` 标记数量为奇数")

    # ---- 标题层级 ----
    headings = [n for n in doc.children if isinstance(n, Heading)]
    stats["headings"] = len(headings)
    if headings and headings[0].level != 1:
        report.warnings.append(f"文章缺少一级标题（首个标题是 H{headings[0].level}）")
    prev = 0
    for h in headings:
        text_content = plain_text(h.children).strip()
        if not text_content:
            report.warnings.append(f"存在空标题（H{h.level}）")
        if prev and h.level - prev > 1:
            report.warnings.append(f"标题层级跳级：H{prev} → H{h.level}「{text_content or '?'}」")
        prev = h.level

    # ---- 超长段落 ----
    for node in walk(doc):
        if isinstance(node, Paragraph):
            t = plain_text(node.children)
            if len(t) > max_para:
                report.warnings.append(
                    f"段落过长（{len(t)} 字符，建议 ≤ {max_para}）：{t[:24]}…"
                )

    # ---- 知识点文字密度（按 h2/h3 分组） ----
    section_chars = 0
    section_name = "文章开头"
    for block in doc.children:
        if isinstance(block, Heading) and block.level >= 2:
            if section_chars > max_section and section_name != "文章开头":
                report.warnings.append(
                    f"「{section_name}」文字密度过高（{section_chars} 字符，建议 ≤ {max_section}）"
                )
            section_chars = 0
            section_name = plain_text(block.children).strip() or "?"
        elif isinstance(block, Paragraph):
            section_chars += len(plain_text(block.children))
        elif isinstance(block, ListBlock):
            for item in block.items:
                section_chars += len(plain_text(item.children))
        elif isinstance(block, BlockQuote):
            section_chars += len(plain_text(block.children))
    if section_chars > max_section and section_name != "文章开头":
        report.warnings.append(
            f"「{section_name}」文字密度过高（{section_chars} 字符，建议 ≤ {max_section}）"
        )

    # ---- 公式可渲染性 ----
    try:
        from .renderer.latex import LatexRenderer

        lr = LatexRenderer()
        for idx, node in enumerate(formula_list, start=1):
            err = latex_syntax_check(node.latex)
            if not err:
                _, err = lr.render(node.latex)
            if err:
                preview = node.latex.replace("\n", " ")[:40]
                report.errors.append(f"公式 {idx} 无法渲染（{err}）：${preview}…$")
    except ImportError:
        report.errors.append("matplotlib 未安装，无法验证公式是否可渲染")

    # ---- 图片 ----
    for node in image_list:
        p = resolve_asset(project_root, article_path.parent, node.src)
        if p is None:
            report.errors.append(f"图片不存在：{node.src}")
            continue
        try:
            with Image.open(p) as im:
                im.verify()
        except (UnidentifiedImageError, OSError):
            report.errors.append(f"图片损坏或不是有效图片：{node.src}")

    # ---- 代码块语言 ----
    try:
        from pygments.lexers import get_lexer_by_name, TextLexer
    except ImportError:
        get_lexer_by_name = None
    for node in walk(doc):
        if isinstance(node, CodeBlock) and node.language and get_lexer_by_name:
            try:
                get_lexer_by_name(node.language)
            except Exception:
                report.warnings.append(f"未知的代码语言：{node.language}")

    # ---- 表格列数 ----
    for node in walk(doc):
        if isinstance(node, Table) and len(node.headers) > max_cols:
            report.warnings.append(
                f"表格列数过多（{len(node.headers)} 列，建议 ≤ {max_cols}）"
            )

    report.stats = stats
    return report


def print_report(report: Report) -> None:
    stats = report.stats
    formulas_n = stats.get("formulas", 0)
    images_n = stats.get("images", 0)
    code_n = stats.get("code_blocks", 0)
    tables_n = stats.get("tables", 0)
    print("Knowledge Publisher Check\n")
    print(f"  ✓ Markdown       OK")
    print(f"  ✓ LaTeX          {formulas_n} formulas" if not report.errors else
          f"  ✗ LaTeX          {formulas_n} formulas ({len(report.errors)} errors)")
    print(f"  ✓ Images         {images_n} found")
    print(f"  ✓ Code blocks    {code_n}")
    print(f"  ✓ Tables         {tables_n}")
    if report.warnings:
        print("\n  ⚠ Warning:")
        for w in report.warnings:
            print(f"    {w}")
    if report.errors:
        print("\n  ✗ Error:")
        for e in report.errors:
            print(f"    {e}")
    print()
