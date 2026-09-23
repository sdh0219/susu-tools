"""资源路径解析：图片统一放 assets/images/，系统自动查找。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def resolve_asset(project_root: Path, article_dir: Path, src: str) -> Optional[Path]:
    """按顺序尝试：相对文章目录 → 相对项目根目录。"""
    if not src or src.startswith(("http://", "https://", "data:")):
        return None
    src = src.replace("\\", "/")
    for base in (Path(article_dir), Path(project_root)):
        candidate = (base / src).resolve()
        if candidate.is_file():
            return candidate
    return None
