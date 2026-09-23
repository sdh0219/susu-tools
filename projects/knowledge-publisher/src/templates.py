"""YAML 模板加载与深合并。

样式不写死在代码里：改 templates/douyin/*.yaml 即可换风格。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_project_config(root: Path) -> dict:
    return load_yaml(root / "config" / "global.yaml")


def load_douyin_templates(root: Path, theme: str = "default") -> Dict[str, dict]:
    """返回 {kind: 合并后的配置}。

    先以全局 templates/douyin/ 的 default.yaml + kind 文件为基底，
    theme != default 时再叠加 templates/douyin/<theme>/ 下的同名文件，
    因此主题文件只需写需要覆盖的部分。
    """
    global_dir = root / "templates" / "douyin"
    base = load_yaml(global_dir / "default.yaml")
    kinds = {"default": base}
    for p in sorted(global_dir.glob("*.yaml")):
        if p.stem == "default":
            continue
        kinds[p.stem] = deep_merge(base, load_yaml(p))
    if theme != "default":
        theme_dir = global_dir / theme
        kinds["default"] = deep_merge(kinds["default"], load_yaml(theme_dir / "default.yaml"))
        for p in sorted(theme_dir.glob("*.yaml")):
            if p.stem == "default":
                continue
            kinds[p.stem] = deep_merge(kinds[p.stem], load_yaml(p))
    return kinds
