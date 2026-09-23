"""抖音图文渲染器：把分页结果绘制成 1080×1440（3:4）的 PNG 图集。

技术路线：AST → 分页器 → Canvas Renderer → PNG。
样式全部来自 templates/douyin/*.yaml，不写死在代码里。
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from ..assets import resolve_asset
from ..ast_nodes import (
    BlockQuote, CodeBlock, Document, Emphasis, Heading, HR, Image as ImageNode,
    InlineCode, Link, ListBlock, MathBlock, MathInline, Node, Paragraph,
    Strong, Table, Text, plain_text, walk,
)
from ..paginator import CodeChunk, Page, paginate
from ..parser import parse
from ..templates import load_douyin_templates
from .fonts import get_font, has_cjk
from .latex import LatexRenderer, colorize

log = logging.getLogger(__name__)


def _rgb(color: str, default: tuple = (38, 39, 43)) -> tuple:
    if not color:
        return default
    try:
        s = color.lstrip("#")
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return default


def _split_units(text: str) -> List[str]:
    """把文本切成排版单元：ASCII 按词、CJK 按字，便于换行。"""
    units: List[str] = []
    cur = ""
    for ch in text:
        if ch in " \t\n":
            if cur:
                units.append(cur)
                cur = ""
            continue
        if ord(ch) > 0x2E7F:  # CJK：单字成段
            if cur:
                units.append(cur)
                cur = ""
            units.append(ch)
        else:
            cur += ch
    if cur:
        units.append(cur)
    return units


class DouyinRenderer:
    def __init__(self, project_root: Path, output_dir: Path, theme: str = "default"):
        self.root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.theme = theme
        self.tpl = load_douyin_templates(self.root, theme)
        self.formulas = LatexRenderer(cache_dir=self.output_dir / "formulas")
        self._font_cache: Dict[tuple, object] = {}
        self._img_cache: Dict[str, Optional[Image.Image]] = {}
        self._lexer_cache: Dict[str, object] = {}
        self._canvas: Image.Image | None = None
        self._draw: ImageDraw.ImageDraw | None = None
        self._article_dir: Path | None = None
        self._total = 0

    # ---------------- 基础工具 ----------------

    def cfg(self, kind: str) -> dict:
        return self.tpl.get(kind, self.tpl["default"])

    def font(self, kind: str, size: int, bold: bool = False):
        key = (kind, size, bold)
        if key not in self._font_cache:
            self._font_cache[key] = get_font(self.root, kind, int(size), bold)
        return self._font_cache[key]

    def content_width(self, cfg: dict) -> int:
        c = cfg["canvas"]
        p = cfg["padding"]
        return int(c["width"]) - int(p["left"]) - int(p["right"])

    def fits_page(self, page: Page, h: float, content_h: float) -> bool:
        return page.used + h <= content_h

    def measure_inline_height(self, node: Node) -> float:
        cfg = self.cfg("default")
        fsize = int(cfg["fonts"]["body"])
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.62))
        if isinstance(node, (Text, InlineCode)):
            return fsize * lf
        if isinstance(node, MathInline):
            return fsize * 1.25
        kids = getattr(node, "children", [])
        return max([self.measure_inline_height(k) for k in kids], default=fsize * lf)

    # ---------------- 公式 ----------------

    def _formula_image(self, latex: str, cfg: dict, inline: bool,
                       maxw: int) -> Tuple[Optional[Image.Image], str]:
        raw, err = self.formulas.render(latex)
        if raw is None:
            return None, err
        img = colorize(raw, _rgb(cfg["colors"].get("formula_text", "#101828")))
        if inline:
            target_h = int(cfg["fonts"]["body"]) * 1.25
        else:
            target_h = int(cfg["fonts"]["formula"]) * 1.35
        w = max(1, int(img.width * target_h / img.height))
        if w > maxw:
            w = maxw
            target_h = max(4, int(img.height * w / img.width))
        return img.resize((int(w), int(target_h)), Image.LANCZOS), ""

    def measure_math(self, block: MathBlock) -> float:
        cfg = self.cfg("formula")
        img, _ = self._formula_image(block.latex, cfg, inline=False,
                                     maxw=self.content_width(cfg))
        h = img.height if img else 140
        return h + 64 + float(cfg.get("spacing", {}).get("block_gap", 24))

    # ---------------- 行内排版 ----------------

    def _segments(self, node: Node, cfg: dict, fsize: int, bold: bool,
                  color: tuple, code: bool, maxw: int) -> List[tuple]:
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.62))
        if isinstance(node, Text):
            out = []
            for unit in _split_units(node.text):
                if code:
                    f = (self.font("code", fsize, bold) if not has_cjk(unit)
                         else self.font("body", fsize, bold))
                else:
                    f = self.font("body", fsize, bold)
                out.append(("text", unit, f.getlength(unit), fsize * lf, f, color))
            return out
        if isinstance(node, Strong):
            return self._segments(node.children, cfg, fsize, True, color, code, maxw)
        if isinstance(node, Emphasis):
            return self._segments(node.children, cfg, fsize, bold, color, code, maxw)
        if isinstance(node, Link):
            accent = _rgb(cfg["colors"].get("accent", "#1667D9"))
            return self._segments(node.children, cfg, fsize, bold, accent, code, maxw)
        if isinstance(node, InlineCode):
            f = (self.font("code", fsize, bold) if not has_cjk(node.text)
                 else self.font("body", fsize, bold))
            c = _rgb(cfg["colors"].get("code_text", "#334155"))
            return [("text", node.text, f.getlength(node.text), fsize * lf, f, c)]
        if isinstance(node, MathInline):
            img, err = self._formula_image(node.latex, cfg, inline=True, maxw=maxw)
            if img:
                return [("image", img, img.width, img.height, None, None)]
            f = self.font("body", fsize, bold)
            return [("text", "[公式错误]", f.getlength("[公式错误]"), fsize * lf, f, (200, 40, 40))]
        if isinstance(node, ImageNode):
            im = self._load_image(node.src)
            if im:
                h = min(fsize * 2.2, int(im.height * (fsize * 2.2) / max(im.width, 1)))
                w = min(maxw, int(im.width * h / max(im.height, 1)))
                h = int(im.height * w / max(im.width, 1))
                return [("image", im.resize((w, h), Image.LANCZOS), w, h, None, None)]
        return []

    def _wrap(self, nodes: List[Node], first_max_w: float, rest_max_w: float,
              indent: float, cfg: dict, fsize: int, bold: bool = False,
              color_key: str = "text", code: bool = False) -> Tuple[List[list], List[float], float]:
        """行内节点排版为多行。返回 (lines, line_heights, total_height)。"""
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.62))
        color = _rgb(cfg["colors"].get(color_key, "#26272B"))
        lines: List[list] = []
        cur: List[tuple] = []
        cur_w = 0.0
        for node in nodes:
            maxw = first_max_w if not lines else rest_max_w
            for seg in self._segments(node, cfg, fsize, bold, color, code, maxw):
                maxw = first_max_w if not lines else rest_max_w
                if cur and cur_w + seg[2] > maxw:
                    lines.append(cur)
                    cur = []
                    cur_w = 0.0
                if not cur and seg[2] > maxw:
                    lines.append([seg])
                    continue
                cur.append(seg)
                cur_w += seg[2]
        if cur:
            lines.append(cur)
        heights = [max(s[3] for s in line) for line in lines]
        return lines, heights, sum(heights)

    def _paste_alpha(self, img: Image.Image, x: int, y: int) -> None:
        """把图片（RGBA 公式 / RGB 行内图）合成到 RGB 画布上。"""
        if img.mode != "RGBA":
            self._canvas.paste(img, (x, y))
            return
        region = self._canvas.crop((x, y, x + img.width, y + img.height)).convert("RGBA")
        region = Image.alpha_composite(region, img)
        self._canvas.paste(region.convert("RGB"), (x, y))

    def _draw_line(self, d: ImageDraw.ImageDraw, line: List[tuple],
                   x: float, y: float, line_h: float) -> None:
        cx = x
        for seg in line:
            if seg[0] == "image":
                img = seg[1]
                self._paste_alpha(img, int(cx), int(y + (line_h - seg[3]) / 2))
            else:
                d.text((cx, y + (line_h - seg[3]) / 2), seg[1], font=seg[4], fill=seg[5])
            cx += seg[2]

    # ---------------- 图片 ----------------

    def _load_image(self, src: str) -> Optional[Image.Image]:
        if src in self._img_cache:
            return self._img_cache[src]
        img = None
        if self._article_dir:
            p = resolve_asset(self.root, self._article_dir, src)
            if p:
                try:
                    img = Image.open(p).convert("RGB")
                except Exception:
                    img = None
        self._img_cache[src] = img
        return img

    def _scaled_image(self, node: ImageNode, cfg: dict) -> Optional[Image.Image]:
        im = self._load_image(node.src)
        if im is None:
            return None
        maxw = self.content_width(cfg)
        max_h = 520
        f = min(maxw / im.width, max_h / im.height, 1.0)
        return im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS)

    # ---------------- 测量（分页器使用，与绘制严格一致） ----------------

    def _heading_layout(self, block: Heading, cfg: dict):
        """标题排版：识别「1. 」式编号 → 编号用强调色，其余常规。返回 (lines, heights, total, num_width, has_num)。"""
        text = plain_text(block.children)
        fsize = int(cfg["fonts"]["heading"] if block.level == 2 else cfg["fonts"]["sub_heading"])
        maxw = self.content_width(cfg)
        m = re.match(r"^(\d+)\s*[.、．]?\s*", text)
        if m:
            f = self.font("body", fsize, True)
            num_width = f.getlength(m.group(1) + ".")
            lines, heights, total = self._wrap([Text(text[m.end():])], maxw - num_width - 18,
                                               maxw, 0, cfg, fsize, bold=True)
            return lines, heights, total, num_width, True
        lines, heights, total = self._wrap([Text(text)], maxw - 30, maxw, 0, cfg, fsize, bold=True)
        return lines, heights, total, 0.0, False

    def measure_heading(self, block: Heading) -> float:
        cfg = self.cfg("default")
        gap = float(cfg.get("spacing", {}).get("section_gap", 60))
        _, _, total, _, _ = self._heading_layout(block, cfg)
        if block.level == 2:
            return total + gap
        return total + gap * 0.7

    def measure_block(self, block: Node) -> float:
        cfg = self.cfg("default")
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        maxw = self.content_width(cfg)
        if isinstance(block, Paragraph):
            fsize = int(cfg["fonts"]["body"])
            _, _, total = self._wrap(block.children, maxw, maxw, 0, cfg, fsize)
            return total + gap
        if isinstance(block, ListBlock):
            return self._measure_list(block, cfg) + gap
        if isinstance(block, BlockQuote):
            fsize = int(cfg["fonts"]["body"])
            _, _, total = self._wrap(block.children, maxw - 28, maxw - 28, 0, cfg, fsize,
                                     color_key="text_secondary")
            return total + 36 + gap
        if isinstance(block, ImageNode):
            im = self._scaled_image(block, cfg)
            h = im.height if im else 180
            caption = block.alt.strip()
            if caption:
                h += 14 + int(cfg["fonts"]["small"]) * 1.4
            return h + gap
        if isinstance(block, HR):
            return 40 + gap
        return gap

    def _measure_list(self, block: ListBlock, cfg: dict) -> float:
        fsize = int(cfg["fonts"]["body"])
        maxw = self.content_width(cfg)
        bullet_w = fsize * 1.2 + 12
        total = 0.0
        for item in block.items:
            nodes = self._item_nodes(item)
            _, _, t = self._wrap(nodes, maxw - bullet_w, maxw, bullet_w, cfg, fsize)
            total += t + 10
        return total

    def measure_code(self, block: CodeBlock) -> float:
        cfg = self.cfg("code")
        fsize = self._code_fsize(cfg, block.content)
        lines = block.content.split("\n")
        return self._code_h(cfg, fsize, len(lines))

    def measure_code_chunk(self, chunk: CodeChunk) -> float:
        cfg = self.cfg("code")
        fsize = self._code_fsize(cfg, "\n".join(chunk.lines))
        return self._code_h(cfg, fsize, len(chunk.lines))

    def _code_h(self, cfg: dict, fsize: int, n_lines: int) -> float:
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.5))
        pad_y = int(cfg.get("code_padding", {}).get("y", 26))
        header_h = fsize * 1.7
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        return pad_y * 2 + header_h + n_lines * (fsize * lf) + gap

    def _code_fsize(self, cfg: dict, content: str) -> int:
        fsize = int(cfg["fonts"]["code"])
        if not content:
            return fsize
        maxw = self.content_width(cfg) - int(cfg.get("code_padding", {}).get("x", 32)) * 2
        f = self.font("code", fsize)
        longest = max(len(l) for l in content.split("\n"))
        line_w = f.getlength(longest * "W")
        if line_w > maxw:
            fsize = max(18, int(fsize * maxw / line_w))
        return fsize

    def max_code_lines(self, content_h: float) -> int:
        cfg = self.cfg("code")
        fsize = int(cfg["fonts"]["code"])
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.5))
        pad_y = int(cfg.get("code_padding", {}).get("y", 26))
        header_h = fsize * 1.7
        return max(1, int((content_h - pad_y * 2 - header_h) / (fsize * lf)))

    def measure_table(self, block: Table) -> float:
        cfg = self.cfg("default")
        maxw = self.content_width(cfg)
        col_ws, fsize = self._table_layout(block, cfg, int(cfg["fonts"]["small"]), maxw)
        total = self._table_row_h(block.headers, col_ws, fsize, cfg, header=True)
        for row in block.rows:
            total += self._table_row_h(row, col_ws, fsize, cfg)
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        return total + gap

    def max_table_rows(self, content_h: float) -> int:
        cfg = self.cfg("default")
        maxw = self.content_width(cfg)
        fsize = max(18, int(cfg["fonts"]["small"]))
        return max(1, int(content_h / (fsize * 1.7 + 12)))

    def _table_layout(self, block: Table, cfg: dict, fsize: int, maxw: int) -> Tuple[List[int], int]:
        pad_x = 12
        ncols = max([len(block.headers)] + [len(r) for r in block.rows] + [1])
        for _ in range(3):
            col_ws = [0] * ncols
            for cells in [block.headers] + list(block.rows):
                for ci, cell in enumerate(cells[:ncols]):
                    lines, _, _ = self._wrap(cell, 10 ** 6, 10 ** 6, 0, cfg, fsize)
                    line_w = sum(s[2] for s in lines[0]) if lines else 0
                    col_ws[ci] = max(col_ws[ci], line_w + pad_x * 2)
            if sum(col_ws) <= maxw:
                break
            fsize = max(18, int(fsize * maxw / max(sum(col_ws), 1)))
        return col_ws, fsize

    def _table_row_h(self, cells: List[List[Node]], col_ws: List[int], fsize: int,
                     cfg: dict, header: bool = False) -> float:
        h = 0.0
        for ci, cell in enumerate(cells[:len(col_ws)]):
            _, _, total = self._wrap(cell, col_ws[ci] - 20, col_ws[ci] - 20, 0, cfg,
                                     fsize, bold=header,
                                     color_key="table_header_text" if header else "text")
            h = max(h, total)
        return h + 8

    # ---------------- 绘制 ----------------

    def _item_nodes(self, item) -> List[Node]:
        out: List[Node] = []
        for child in item.children:
            if isinstance(child, Paragraph):
                out.extend(child.children)
            elif isinstance(child, ListBlock):
                for sub in child.items:
                    out.append(Text("· " + plain_text(sub.children) + "  "))
            else:
                out.extend(getattr(child, "children", []))
        return out

    def _draw_heading(self, d: ImageDraw.ImageDraw, block: Heading, x: float,
                      y: float, maxw: float, cfg: dict) -> float:
        text = plain_text(block.children)
        accent = _rgb(cfg["colors"]["accent"])
        lines, heights, _, num_width, has_num = self._heading_layout(block, cfg)
        if block.level == 2 and has_num:
            f = self.font("body", int(cfg["fonts"]["heading"]), True)
            m = re.match(r"^(\d+)\s*[.、．]?\s*", text)
            d.text((x, y), m.group(1) + ".", font=f, fill=accent)
            lx = x + num_width + 18
        elif block.level == 2:
            d.rounded_rectangle([x, y + 8, x + 8, y + int(cfg["fonts"]["heading"]) * 0.75],
                                radius=4, fill=accent)
            lx = x + 26
        else:
            fsize = int(cfg["fonts"]["sub_heading"])
            d.ellipse([x, y + fsize * 0.28, x + 12, y + fsize * 0.28 + 12], fill=accent)
            lx = x + 26
        for k, line in enumerate(lines):
            self._draw_line(d, line, lx, y, heights[k])
            y += heights[k]
        gap = float(cfg.get("spacing", {}).get("section_gap", 60))
        if block.level == 2:
            return y + gap
        return y + gap * 0.7

    def _draw_paragraph(self, d: ImageDraw.ImageDraw, block: Paragraph, x: float,
                        y: float, maxw: float, cfg: dict) -> float:
        fsize = int(cfg["fonts"]["body"])
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        lines, heights, _ = self._wrap(block.children, maxw, maxw, 0, cfg, fsize)
        for k, line in enumerate(lines):
            self._draw_line(d, line, x, y, heights[k])
            y += heights[k]
        return y + gap

    def _draw_math(self, d: ImageDraw.ImageDraw, block: MathBlock, x: float,
                   y: float, maxw: float) -> float:
        cfg = self.cfg("formula")
        img, err = self._formula_image(block.latex, cfg, inline=False, maxw=maxw - 96)
        gap = float(cfg.get("spacing", {}).get("block_gap", 24))
        if img is None:
            d.text((x, y), f"[公式渲染失败: {err}]", font=self.font("body", 28),
                   fill=(200, 40, 40))
            return y + 60 + gap
        panel = cfg["colors"].get("formula_panel")
        ph = img.height + 64
        # 通栏公式卡片：整行宽度，公式居中
        d.rounded_rectangle([x, y, x + maxw, y + ph], radius=24, fill=_rgb(panel))
        self._paste_alpha(img, int(x + (maxw - img.width) / 2),
                          int(y + (ph - img.height) / 2))
        return y + ph + gap

    def _code_tokens(self, lang: str, lines: List[str]) -> List[List[Tuple[object, str]]]:
        key = lang or ""
        if key not in self._lexer_cache:
            try:
                from pygments.lexers import get_lexer_by_name
                self._lexer_cache[key] = get_lexer_by_name(key) if key else None
            except Exception:
                self._lexer_cache[key] = None
        lexer = self._lexer_cache[key]
        if lexer is None:
            return [[(None, ln)] for ln in lines]
        result: List[List[Tuple[object, str]]] = []
        cur_line: List[Tuple[object, str]] = []
        for ttype, tok in lexer.get_tokens("\n".join(lines)):
            parts = tok.split("\n")
            for pi, part in enumerate(parts):
                if pi > 0:
                    result.append(cur_line)
                    cur_line = []
                if part:
                    cur_line.append((ttype, part))
        if cur_line:
            result.append(cur_line)
        return result

    def _token_color(self, ttype) -> tuple:
        try:
            from pygments.styles import get_style_by_name
            style_name = self.cfg("code").get("pygments_style", "friendly")
            key = f"__style__{style_name}"
            style = self._lexer_cache.get(key)
            if style is None:
                style = get_style_by_name(style_name)
                self._lexer_cache[key] = style
            c = style.style_for_token(ttype)["color"]
            if c:
                return _rgb("#" + c, (226, 232, 240))
        except Exception:
            pass
        return _rgb(self.cfg("code")["colors"].get("code_text", "#E2E8F0"))

    def _draw_code(self, d: ImageDraw.ImageDraw, block, x: float, y: float,
                   maxw: float) -> float:
        cfg = self.cfg("code")
        if isinstance(block, CodeChunk):
            lines = block.lines
            content = "\n".join(lines)
            label = f"{block.language or 'code'} · {block.index}/{block.total}"
        else:
            lines = block.content.split("\n")
            content = block.content
            label = block.language or "code"
        fsize = self._code_fsize(cfg, content)
        lf = float(cfg.get("spacing", {}).get("line_factor", 1.5))
        line_h = fsize * lf
        pad_x = int(cfg.get("code_padding", {}).get("x", 32))
        pad_y = int(cfg.get("code_padding", {}).get("y", 26))
        header_h = fsize * 1.7
        panel_h = pad_y * 2 + header_h + len(lines) * line_h
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        bg = _rgb(cfg["colors"].get("code_background", "#0F172A"))
        d.rounded_rectangle([x, y, x + maxw, y + panel_h], radius=20, fill=bg)
        fh = self.font("body", max(20, int(fsize * 0.78)), True)
        d.text((x + pad_x, y + pad_y + 4), label,
               font=fh, fill=_rgb(cfg["colors"].get("code_header_text", "#94A3B8")))
        ty = y + pad_y + header_h
        for tl in self._code_tokens(block.language, lines):
            tx = x + pad_x
            for ttype, tok in tl:
                color = self._token_color(ttype)
                f = (self.font("code", fsize) if not has_cjk(tok)
                     else self.font("body", fsize))
                d.text((tx, ty), tok, font=f, fill=color)
                tx += f.getlength(tok)
            ty += line_h
        return y + panel_h + gap

    def _draw_table(self, d: ImageDraw.ImageDraw, block: Table, x: float,
                    y: float, maxw: float, cfg: dict) -> float:
        col_ws, fsize = self._table_layout(block, cfg, int(cfg["fonts"]["small"]), maxw)
        header_bg = _rgb(cfg["colors"].get("table_header_background", "#1667D9"))
        alt_bg = _rgb(cfg["colors"].get("table_alt_background", "#FAFBFC"))
        text_color = _rgb(cfg["colors"]["text"])
        header_color = _rgb(cfg["colors"].get("table_header_text", "#FFFFFF"))
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))

        def draw_cells(cells, row_y, bg, bold, color_key):
            d.rectangle([x, row_y, x + sum(col_ws), row_y + rh], fill=bg)
            rx = x
            for ci, cell in enumerate(cells[:len(col_ws)]):
                lines, heights, _ = self._wrap(cell, col_ws[ci] - 20, col_ws[ci] - 20, 0,
                                               cfg, fsize, bold=bold, color_key=color_key)
                cy = row_y + 4
                for k, line in enumerate(lines):
                    self._draw_line(d, line, rx + 10, cy, heights[k])
                    cy += heights[k]
                rx += col_ws[ci]

        rh = self._table_row_h(block.headers, col_ws, fsize, cfg, header=True)
        draw_cells(block.headers, y, header_bg, True, "table_header_text")
        y += rh
        for ri, row in enumerate(block.rows):
            rh = self._table_row_h(row, col_ws, fsize, cfg)
            bg = alt_bg if ri % 2 == 1 else _rgb(cfg["colors"]["background"])
            draw_cells(row, y, bg, False, "text")
            y += rh
        return y + gap

    def _draw_list(self, d: ImageDraw.ImageDraw, block: ListBlock, x: float,
                   y: float, maxw: float, cfg: dict) -> float:
        fsize = int(cfg["fonts"]["body"])
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        bullet_w = fsize * 1.2 + 12
        accent = _rgb(cfg["colors"]["accent"])
        for idx, item in enumerate(block.items):
            nodes = self._item_nodes(item)
            lines, heights, _ = self._wrap(nodes, maxw - bullet_w, maxw, bullet_w,
                                           cfg, fsize)
            bullet = f"{block.start + idx}." if block.ordered else "•"
            fb = self.font("body", fsize, True)
            d.text((x, y + (heights[0] - fsize) / 2), bullet, font=fb, fill=accent)
            for k, line in enumerate(lines):
                self._draw_line(d, line, x + bullet_w, y, heights[k])
                y += heights[k]
            y += 10
        return y + gap

    def _draw_quote(self, d: ImageDraw.ImageDraw, block: BlockQuote, x: float,
                    y: float, maxw: float, cfg: dict) -> float:
        fsize = int(cfg["fonts"]["body"])
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        lines, heights, total = self._wrap(block.children, maxw - 28, maxw - 28, 0, cfg,
                                           fsize, color_key="text_secondary")
        pad = 18
        d.rounded_rectangle([x, y, x + maxw, y + total + pad * 2], radius=14,
                            fill=_rgb(cfg["colors"].get("quote_background", "#F7F8FA")))
        d.rounded_rectangle([x + 6, y + pad - 6, x + 14, y + total + pad + 6],
                            radius=4, fill=_rgb(cfg["colors"]["accent"]))
        cy = y + pad
        for k, line in enumerate(lines):
            self._draw_line(d, line, x + 28, cy, heights[k])
            cy += heights[k]
        return y + total + pad * 2 + gap

    def _draw_image(self, d: ImageDraw.ImageDraw, block: ImageNode, x: float,
                    y: float, maxw: float, cfg: dict) -> float:
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        im = self._scaled_image(block, cfg)
        if im is None:
            d.rounded_rectangle([x, y, x + maxw, y + 180], radius=16,
                                fill=_rgb(cfg["colors"].get("quote_background", "#F7F8FA")))
            d.text((x + 24, y + 76), f"图片缺失：{block.src}", font=self.font("body", 28),
                   fill=_rgb(cfg["colors"].get("text_secondary", "#667085")))
            return y + 180 + gap
        px = x + (maxw - im.width) / 2
        self._canvas.paste(im, (int(px), int(y)))
        y += im.height
        caption = block.alt.strip()
        if caption:
            y += 14
            f = self.font("body", int(cfg["fonts"]["small"]))
            w = f.getlength(caption)
            d.text((x + (maxw - w) / 2, y), caption, font=f,
                   fill=_rgb(cfg["colors"].get("text_secondary", "#667085")))
            y += int(cfg["fonts"]["small"]) * 1.4
        return y + gap

    def _draw_hr(self, d: ImageDraw.ImageDraw, x: float, y: float, maxw: float,
                 cfg: dict) -> float:
        gap = float(cfg.get("spacing", {}).get("block_gap", 22))
        d.line([(x, y + 18), (x + maxw, y + 18)], fill=_rgb(cfg["colors"].get("divider", "#E5E7EB")),
               width=2)
        return y + 40 + gap

    # ---------------- 整页绘制 ----------------

    def _cover_info(self, doc: Document, meta: dict) -> dict:
        title = str(meta.get("title") or "").strip()
        if not title:
            for b in doc.children:
                if isinstance(b, Heading) and b.level == 1:
                    title = plain_text(b.children).strip()
                    break
        subtitle = str(meta.get("subtitle") or "").strip()
        if not subtitle:
            for b in doc.children:
                if isinstance(b, Paragraph):
                    subtitle = plain_text(b.children).strip()
                    break
            if len(subtitle) > 60:
                subtitle = subtitle[:60] + "…"
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip() for t in tags if str(t).strip()]
        return {
            "title": title or "未命名文章",
            "subtitle": subtitle,
            "series": str(meta.get("series") or "").strip(),
            "author": str(meta.get("author") or "").strip(),
            "tags": tags[:6],
        }

    def render_page(self, page: Page, cover_info: dict) -> Image.Image:
        kind = page.kind
        cfg = self.cfg("cover" if kind == "cover" else "summary" if kind == "summary" else "default")
        W = int(cfg["canvas"]["width"])
        H = int(cfg["canvas"]["height"])
        canvas = Image.new("RGB", (W, H), _rgb(cfg["colors"]["background"]))
        self._canvas = canvas
        d = ImageDraw.Draw(canvas)
        self._draw = d
        pad = cfg["padding"]
        maxw = W - int(pad["left"]) - int(pad["right"])
        if kind == "cover":
            self._draw_cover(d, cover_info, cfg)
        elif kind == "summary":
            self._draw_summary(d, cfg)
        else:
            # 顶部进度条（内容页：当前进度）
            frac = (page.index - 1) / max(self._total - 1, 1)
            d.rectangle([0, 0, int(W * frac), 6], fill=_rgb(cfg["colors"]["accent"]))
            y = int(pad["top"])
            for block in page.blocks:
                x = int(pad["left"])
                if isinstance(block, Heading):
                    y = self._draw_heading(d, block, x, y, maxw, cfg)
                elif isinstance(block, Paragraph):
                    y = self._draw_paragraph(d, block, x, y, maxw, cfg)
                elif isinstance(block, MathBlock):
                    y = self._draw_math(d, block, x, y, maxw)
                elif isinstance(block, (CodeBlock, CodeChunk)):
                    y = self._draw_code(d, block, x, y, maxw)
                elif isinstance(block, Table):
                    y = self._draw_table(d, block, x, y, maxw, cfg)
                elif isinstance(block, ListBlock):
                    y = self._draw_list(d, block, x, y, maxw, cfg)
                elif isinstance(block, BlockQuote):
                    y = self._draw_quote(d, block, x, y, maxw, cfg)
                elif isinstance(block, ImageNode):
                    y = self._draw_image(d, block, x, y, maxw, cfg)
                elif isinstance(block, HR):
                    y = self._draw_hr(d, x, y, maxw, cfg)
        # 页脚
        if kind != "cover":
            # 页码胶囊（右下）
            f = self.font("body", 26, True)
            num = f"{page.index:02d} / {self._total:02d}"
            w = f.getlength(num) + 40
            chip = _rgb(cfg["colors"].get("footer_chip", "#EDF3FC"))
            d.rounded_rectangle([W - int(pad["right"]) - w, H - int(pad["bottom"]) - 50,
                                 W - int(pad["right"]), H - int(pad["bottom"]) - 10],
                                radius=20, fill=chip)
            d.text((W - int(pad["right"]) - w + 20, H - int(pad["bottom"]) - 43), num,
                   font=f, fill=_rgb(cfg["colors"]["accent"]))
            # 品牌（左下，小字）
            d.text((int(pad["left"]), H - int(pad["bottom"]) - 34), "Knowledge Publisher",
                   font=self.font("body", 20),
                   fill=_rgb(cfg["colors"].get("footer", "#8FA0B8")))
        return canvas

    def _draw_cover(self, d: ImageDraw.ImageDraw, info: dict, cfg: dict) -> None:
        W, H = self._canvas.size
        pad = cfg["padding"]
        x = int(pad["left"])
        maxw = W - int(pad["left"]) - int(pad["right"])
        accent = _rgb(cfg["colors"]["accent"])
        accent_soft = _rgb(cfg["colors"].get("accent_soft", "#EAF2FE"))
        # 装饰：右上大圆 + 左下小圆
        d.ellipse([W - 460, -200, W + 160, 420], fill=accent_soft)
        d.ellipse([-150, H - 280, 150, H + 20], fill=accent_soft)
        y = int(pad["top"]) + 30
        if info["series"]:
            f = self.font("body", int(cfg["fonts"]["series"]), True)
            w = f.getlength(info["series"]) + 44
            d.rounded_rectangle([x, y, x + w, y + 54], radius=27, fill=accent)
            d.text((x + 22, y + (54 - int(cfg["fonts"]["series"])) / 2), info["series"],
                   font=f, fill=_rgb(cfg["colors"].get("badge_text", "#FFFFFF")))
            y += 54 + 44
        lines, heights, _ = self._wrap([Text(info["title"])], maxw, maxw, 0, cfg,
                                       int(cfg["fonts"]["title"]), bold=True,
                                       color_key="title")
        y += 10
        for k, line in enumerate(lines):
            self._draw_line(d, line, x, y, heights[k])
            y += heights[k]
        y += 22
        d.rounded_rectangle([x, y, x + 140, y + 12], radius=6, fill=accent)
        y += 60
        if info["subtitle"]:
            sub_lines, sub_heights, _ = self._wrap([Text(info["subtitle"])], maxw, maxw, 0,
                                                   cfg, int(cfg["fonts"]["subtitle"]),
                                                   color_key="subtitle")
            for k, line in enumerate(sub_lines):
                self._draw_line(d, line, x, y, sub_heights[k])
                y += sub_heights[k]
        # 标签胶囊（frontmatter tags）
        if info["tags"]:
            y += 34
            f = self.font("body", int(cfg["fonts"].get("tag", 26)))
            chip_h = int(cfg["fonts"].get("tag", 26)) + 24
            tx, ty = x, y
            for tag in info["tags"]:
                tw = f.getlength(tag) + 40
                if tx + tw > x + maxw:
                    tx = x
                    ty += chip_h + 14
                d.rounded_rectangle([tx, ty, tx + tw, ty + chip_h], radius=chip_h / 2,
                                    fill=_rgb(cfg["colors"].get("accent_soft", "#E8F1FE")))
                d.text((tx + 20, ty + 12), tag, font=f, fill=_rgb(cfg["colors"]["accent"]))
                tx += tw + 14
        if info["author"]:
            f = self.font("body", int(cfg["fonts"]["author"]))
            d.text((x, H - int(pad["bottom"]) - 40), f"@{info['author']}", font=f,
                   fill=_rgb(cfg["colors"].get("author", "#98A2B3")))

    def _draw_summary(self, d: ImageDraw.ImageDraw, cfg: dict) -> None:
        W, H = self._canvas.size
        accent = _rgb(cfg["colors"]["accent"])
        accent_soft = _rgb(cfg["colors"].get("accent_soft", "#EAF2FE"))
        texts = cfg.get("texts", {})
        d.ellipse([W / 2 - 300, H * 0.14 - 300, W / 2 + 300, H * 0.14 + 300], fill=accent_soft)

        def center(text: str, fsize: int, color, y: float) -> float:
            f = self.font("body", fsize, True)
            w = f.getlength(text)
            d.text(((W - w) / 2, y), text, font=f, fill=color)
            return y + fsize * 1.6

        y = center(texts.get("thanks", "谢谢观看"), int(cfg["fonts"]["thanks"]),
                   _rgb(cfg["colors"]["title"]), H * 0.42)
        series = texts.get("series")
        if series:
            y = center(series, int(cfg["fonts"]["body"]),
                       _rgb(cfg["colors"]["body"]), y)
        y = center(texts.get("follow", "关注我，持续更新数学与计算机知识"),
                   int(cfg["fonts"]["body"]), accent, y + 10)
        tips = texts.get("tips", [])
        if tips:
            f = self.font("body", int(cfg["fonts"]["body"]))
            total_w = sum(f.getlength(t) + 44 + 18 for t in tips) - 18
            cx = (W - total_w) / 2
            ty = y + 20
            for t in tips:
                w = f.getlength(t) + 44
                d.rounded_rectangle([cx, ty, cx + w, ty + 52], radius=26,
                                    fill=_rgb(cfg["colors"].get("chip", "#FFFFFF")))
                d.text((cx + 22, ty + (52 - int(cfg["fonts"]["body"])) / 2), t,
                       font=f, fill=accent)
                cx += w + 18

    # ---------------- 构建入口 ----------------

    def output_page_dir(self, article_name: str) -> Path:
        """主题输出目录：默认主题直接放 douyin/，命名主题放 douyin/<theme>/。"""
        base = self.output_dir / article_name / "douyin"
        return base if self.theme == "default" else base / self.theme

    def build(self, article_path: Path, meta_override: Optional[dict] = None
              ) -> Tuple[List[Path], List[Page], List[dict]]:
        article_path = Path(article_path)
        self._article_dir = article_path.parent
        text = article_path.read_text(encoding="utf-8")
        doc, meta = parse(text)
        if meta_override:
            meta.update(meta_override)
        pages, outline = paginate(doc, meta, self)
        out_dir = self.output_page_dir(article_path.stem)
        out_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = out_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        cover_info = self._cover_info(doc, meta)
        self._total = len(pages)
        files: List[Path] = []
        for page in pages:
            img = self.render_page(page, cover_info)
            f = out_dir / f"{page.index:02d}.png"
            img.save(f)
            files.append(f)
        # 原始图片归档
        for node in walk(doc):
            if isinstance(node, ImageNode):
                p = resolve_asset(self.root, article_path.parent, node.src)
                if p and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    target = assets_dir / p.name
                    if not target.exists():
                        try:
                            target.write_bytes(p.read_bytes())
                        except OSError:
                            pass
        info = {
            "article": article_path.stem,
            "title": cover_info["title"],
            "total": len(pages),
            "pages": [
                {"index": p.index, "kind": p.kind, "file": f"{p.index:02d}.png",
                 "types": [type(b).__name__ for b in p.blocks]}
                for p in pages
            ],
            "outline": outline,
        }
        (out_dir / "pages.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        return files, pages, outline

    def build_if_stale(self, article_path: Path) -> List[Path]:
        out_dir = self.output_page_dir(article_path.stem)
        marker = out_dir / "pages.json"
        stale = not marker.exists() or article_path.stat().st_mtime > marker.stat().st_mtime
        if not stale:
            # 模板 YAML 变更也要触发重建
            tpl_dir = self.root / "templates" / "douyin"
            newest = max((p.stat().st_mtime for p in tpl_dir.rglob("*.yaml")), default=0)
            if newest > marker.stat().st_mtime:
                stale = True
        if not stale:
            return sorted(out_dir.glob("*.png"))
        files, _, _ = self.build(article_path)
        return files
