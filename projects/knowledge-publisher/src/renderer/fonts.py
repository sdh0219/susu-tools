"""中英文字体发现。

优先使用 assets/fonts/ 下的自定义字体，其次系统字体：
Windows → 微软雅黑 / Consolas；Linux/macOS → 常见字体目录。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from PIL import ImageFont

_BODY_CANDIDATES = ["msyh.ttc", "msyhl.ttc", "simhei.ttf", "msjh.ttc"]
_BODY_BOLD_CANDIDATES = ["msyhbd.ttc", "msyh.ttc", "simhei.ttf", "msjhbd.ttc"]
_CODE_CANDIDATES = ["consola.ttf", "consolab.ttf", "cour.ttf", "msyh.ttc"]

_font_cache: Dict[tuple, ImageFont.FreeTypeFont] = {}


def _search_paths(project_root: Path) -> List[Path]:
    paths = [Path(project_root) / "assets" / "fonts"]
    if os.name == "nt":
        windir = os.environ.get("WINDIR", "C:/Windows")
        paths.append(Path(windir) / "Fonts")
    else:
        for d in ("/usr/share/fonts/truetype", "/usr/share/fonts/opentype",
                  "/System/Library/Fonts"):
            paths.append(Path(d))
    return paths


def _find(candidates: List[str], paths: List[Path]) -> Optional[Path]:
    for name in candidates:
        for d in paths:
            p = d / name
            if p.is_file():
                return p
    return None


def get_font(project_root: Path, kind: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (str(project_root), kind, size, bold)
    if key in _font_cache:
        return _font_cache[key]
    if kind == "code":
        candidates = _CODE_CANDIDATES
    elif kind == "body" and bold:
        candidates = _BODY_BOLD_CANDIDATES
    else:
        candidates = _BODY_CANDIDATES
    path = _find(candidates, _search_paths(project_root))
    if path is None:
        raise RuntimeError(
            f"未找到可用字体（kind={kind}），请将字体文件放入 assets/fonts/ 目录"
        )
    font = ImageFont.truetype(str(path), size)
    _font_cache[key] = font
    return font


def has_cjk(text: str) -> bool:
    """是否包含 CJK（中文/日文/韩文）字符，用于代码块内中英文混排的字体切换。"""
    return any(
        "\u2E80" <= ch <= "\u9FFF" or "\uF900" <= ch <= "\uFAFF" or "\uFF00" <= ch <= "\uFFEF"
        for ch in text
    )
