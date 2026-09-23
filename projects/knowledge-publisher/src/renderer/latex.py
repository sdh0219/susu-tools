"""LaTeX → PNG 公式渲染。

技术路线：LaTeX → matplotlib mathtext → PNG（确定性输出，无网络依赖）。
V2.0 可平滑替换为 KaTeX/MathJax 服务端渲染。
"""
from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
from matplotlib import mathtext
from PIL import Image

_WS_RE = re.compile(r"\s+")


def _trim(img: Image.Image, pad: int = 6) -> Image.Image:
    bbox = img.getbbox()
    if bbox is None:
        return img
    w, h = img.size
    bbox = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(w, bbox[2] + pad),
        min(h, bbox[3] + pad),
    )
    return img.crop(bbox)


def colorize(img: Image.Image, rgb: tuple) -> Image.Image:
    """把公式从黑色染成模板指定的颜色（保留透明度）。"""
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    r = r.point(lambda _: rgb[0])
    g = g.point(lambda _: rgb[1])
    b = b.point(lambda _: rgb[2])
    return Image.merge("RGBA", (r, g, b, a))


class LatexRenderer:
    """带内存缓存（+ 磁盘缓存）的公式渲染器。"""

    def __init__(self, cache_dir: Optional[Path] = None, dpi: int = 400):
        self.dpi = dpi
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Tuple[bool, object]] = {}

    def render(self, latex: str) -> Tuple[Optional[Image.Image], str]:
        """返回 (PIL.Image | None, error)。"""
        latex = _WS_RE.sub(" ", latex.strip())
        if not latex:
            return None, "空公式"
        if latex in self._cache:
            ok, val = self._cache[latex]
            return (val.copy(), "") if ok else (None, val)

        if self.cache_dir:
            name = "f" + hashlib.sha1(latex.encode("utf-8")).hexdigest()[:12] + ".png"
            disk = self.cache_dir / name
        else:
            disk = None

        try:
            buf = io.BytesIO()
            mathtext.math_to_image(latex, buf, dpi=self.dpi, format="png")
            buf.seek(0)
            img = Image.open(buf).convert("RGBA")
            img = _trim(img)
            if disk:
                img.save(disk)
            self._cache[latex] = (True, img)
            return img.copy(), ""
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            self._cache[latex] = (False, msg)
            return None, msg
