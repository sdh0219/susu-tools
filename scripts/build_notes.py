#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_notes.py — 把 1_learning/rivew-应大 下的复习笔记转成静态站点页面。

用法:
    python scripts/build_notes.py [--source DIR] [--out DIR]

默认源目录:  <仓库>/../../1_learning/rivew-应大  (仓库外, 只读)
默认输出:    <仓库>/web/notes/{slug}.html + {slug}.md (md 原样拷贝, 供下载)
重复运行幂等: 输出不依赖时间戳, 内容只由源文件决定。

⚠️ 重新生成会覆盖 web/notes/ 下的手改内容。2026-11 优化工作流的多数修复
（表格转换、错误解析文案等）只改了 HTML 产物——重生成前先 git diff 对照,
需要保留的手改应回流到本脚本或源 md。
"""

import argparse
import html
import math
import re
import shutil
import sys
from pathlib import Path

import markdown

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT.parent.parent / "1_learning" / "rivew-应大"
DEFAULT_OUT = REPO_ROOT / "web" / "notes"

# slug / 课程名 —— 见任务说明
NOTES = [
    {
        "source": "习思想/一周复习冲刺文档.md",
        "slug": "socialism-theory-sprint",
        "course": "新时代中国特色社会主义理论与实践",
    },
    {
        "source": "习思想/以题代练题库.md",
        "slug": "socialism-theory-question-bank",
        "course": "新时代中国特色社会主义理论与实践",
    },
    {
        "source": "综合英语/综合英语期末复习大纲.md",
        "slug": "comprehensive-english-outline",
        "course": "研究生综合英语",
    },
    {
        "source": "论文写作道德/论文写作与学术道德规范-复习总结.md",
        "slug": "academic-writing-summary",
        "course": "论文写作与学术道德",
    },
    {
        "source": "数值计算实验与数学建模/练习题-详细答案解析.md",
        "slug": "numerical-computing-exercises",
        "course": "数值计算实验与数学建模",
    },
]

# 相对链接改写规则
INTERNAL_LINK_MAP = {
    # 指向配套冲刺文档的相对链接 → 站内笔记页
    "一周复习冲刺文档.md": "/notes/socialism-theory-sprint.html",
}
LOCAL_EXTS = (".md", ".txt", ".pdf", ".doc", ".docx", ".pptx")
# markdown 输出的锚点都是 <a href="...">...</a> 形式
ANCHOR_RE = re.compile(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
# LaTeX 展示公式 $$...$$: 先转义保护, 否则 markdown 会把公式里的
# w[0,1](t-0) 之类误当成链接吃掉, 下标/尖括号也会被破坏
MATH_BLOCK_RE = re.compile(r"\$\$\s*(.+?)\s*\$\$", re.DOTALL)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{TITLE}} - 自习室 - Susu</title>
  <meta name="description" content="{{COURSE}}复习笔记：{{TITLE}}。由 Susu 整理，考完也不删。">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{{TITLE}} - Susu 自习室">
  <meta property="og:url" content="https://susu-2x9.pages.dev/notes/{{SLUG}}.html">
  <meta property="og:image" content="https://susu-2x9.pages.dev/assets/img/og-cover.jpg">
  <meta property="og:description" content="{{COURSE}}复习笔记：{{TITLE}}。由 Susu 整理，考完也不删。">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="https://susu-2x9.pages.dev/notes/{{SLUG}}.html">
  <link rel="alternate" type="application/rss+xml" title="工具随笔 RSS" href="https://susu-2x9.pages.dev/rss.xml">
  <link rel="stylesheet" href="/assets/css/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌸</text></svg>">
  <script>(function(){try{var t=localStorage.getItem('susu-theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}})();</script>
  <style>
    .note-toc { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 18px 22px; margin: 20px 0 26px; }
    .note-toc-title { font-size: .95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
    .note-toc ul { list-style: none; margin: 0; padding: 0; }
    .note-toc ul ul { padding-left: 1.3em; margin-top: 4px; }
    .note-toc li { margin-bottom: 5px; font-size: .92rem; }
    .note-toc a { color: var(--text-secondary); }
    .note-toc a:hover { color: var(--accent-purple); }
    .note-toc .toc-l1 > a { color: var(--text-primary); font-weight: 600; }
    .essay-body h2 { margin: 30px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--border-color); }
    .essay-body h3 { margin: 24px 0 10px; }
    .essay-body h4 { margin: 18px 0 8px; }
    .essay-body ul, .essay-body ol { margin: 0 0 14px 1.6em; }
    .essay-body li { margin-bottom: 6px; color: var(--text-soft); font-size: .95rem; line-height: 1.85; }
    .essay-body a { color: var(--accent-blue); }
    .essay-body a:hover { text-decoration: underline; }
    .essay-body strong { color: var(--text-primary); }
    .essay-body blockquote { margin: 0 0 16px; padding: 10px 16px; border-left: 3px solid var(--accent-purple); background: var(--bg-secondary); border-radius: 0 8px 8px 0; color: var(--text-secondary); }
    .essay-body blockquote p { font-size: .92rem; margin-bottom: 6px; }
    .essay-body hr { border: 0; border-top: 1px solid var(--border-color); margin: 26px 0; }
    .essay-body code { font-family: Consolas, 'JetBrains Mono', Menlo, monospace; font-size: .88em; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; padding: 1px 6px; color: var(--accent-orange); }
    .essay-body pre { background: #10131a; border: 1px solid var(--border-color); border-radius: 10px; padding: 16px 18px; overflow-x: auto; margin: 0 0 16px; line-height: 1.6; }
    .essay-body pre code { background: none; border: 0; padding: 0; color: #d7dce5; font-size: .88rem; }
    .essay-body .math-block { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px 18px; margin: 0 0 16px; overflow-x: auto; text-align: center; font-family: 'Cambria Math', 'STIX Two Math', 'Times New Roman', serif; font-size: 1rem; color: var(--text-primary); }
    .essay-body table { display: block; width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0 0 16px; font-size: .9rem; }
    .essay-body th, .essay-body td { border: 1px solid var(--border-color); padding: 8px 12px; text-align: left; vertical-align: top; }
    .essay-body th { background: var(--bg-secondary); color: var(--text-primary); font-weight: 600; }
    .essay-body tbody tr:nth-child(even) { background: rgba(128, 128, 128, 0.06); }
    @media (max-width: 768px) { .essay-body h2 { margin: 24px 0 12px; } }
  </style>
</head>
<body>
  <nav class="nav" id="nav"><div class="container">
    <a href="/index.html" class="nav-logo">Susu</a>
    <ul class="nav-links" id="navLinks">
      <li><a href="/index.html">首页</a></li>
      <li><a href="/index.html#projects">作品</a></li>
      <li><a href="/study.html" class="active">自习室</a></li>
      <li><a href="/bangumi.html">追番墙</a></li>
      <li><a href="/gallery.html">画廊</a></li>
      <li><a href="/blog.html">随笔</a></li>
      <li><a href="/index.html#about">关于</a></li>
      <li><a href="/index.html#contact">联系</a></li>
    </ul>
    <div class="nav-right">
      <button class="theme-toggle" id="themeToggle" aria-label="切换主题" title="切换主题">☀️</button>
      <button class="nav-toggle" id="navToggle" type="button" aria-label="打开菜单" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button>
    </div>
  </div></nav>

  <section class="blog-hero"><div class="container"><div class="section-header">
    <div class="section-tag">课程笔记</div>
    <h1 class="section-title">{{TITLE}}</h1>
    <p class="section-desc">{{COURSE}} · 2026 秋 · <a href="/notes/{{SLUG}}.md">下载 Markdown</a> · <a href="/study.html">← 返回自习室</a></p>
  </div></div></section>

  <section class="essays"><div class="container">
    <article class="essay note-page">
      <div class="essay-head">
        <span class="essay-num" aria-hidden="true">📖</span>
        <div class="essay-title-wrap"><h2>{{TITLE}}</h2>
        <div class="essay-meta"><span>2026 秋季学期</span><span>阅读约 {{MINUTES}} 分钟</span></div></div>
      </div>
      {{TOC}}
      <div class="essay-body">{{BODY}}</div>
    </article>
  </div></section>

  <footer class="footer"><div class="container"><p>© 2026 Susu · 所有工具永久免费 · ＼(^o^)／</p></div></footer>

  <script src="/assets/js/main.js"></script>
  <script defer src="/assets/js/live2d.js"></script>
  <script defer src="/assets/js/starfield.js"></script>
  <script defer src="/assets/js/anime-ui.js"></script>
  <script defer src="/assets/js/extras.js"></script>
  {{HEAD_EXTRA}}
</body>
</html>
"""


def doc_title(text: str) -> str:
    """取第一个 `# ` 一级标题作为文档标题。"""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("##"):
            return s[2:].strip()
    return ""


def protect_math(text: str) -> "tuple[str, list]":
    """把 $$...$$ 展示公式换成占位符并暂存, 避免被 markdown 解析破坏。"""
    stash: list = []

    def repl(m: "re.Match[str]") -> str:
        stash.append(m.group(1).strip())
        return f"\n\nMATHBLOCK{len(stash) - 1}PLACEHOLDER\n\n"

    return MATH_BLOCK_RE.sub(repl, text), stash


def restore_math(body_html: str, stash: list) -> str:
    """把占位符换回转义后的公式卡片。"""
    for i, formula in enumerate(stash):
        block = f'<div class="math-block">{html.escape(formula)}</div>'
        para = f"<p>MATHBLOCK{i}PLACEHOLDER</p>"
        if para in body_html:
            body_html = body_html.replace(para, block)
        else:
            body_html = body_html.replace(f"MATHBLOCK{i}PLACEHOLDER", block)
    return body_html


def demote_headings(body_html: str) -> str:
    """正文标题整体降一级（h1→h2 …）：源 md 的 # 会渲染成 h1，与 hero 的 h1 重复，
    读屏大纲出现 h1→h2→h1 倒挂。id 不动，目录锚点不受影响。"""
    return re.sub(r"(</?h)([1-5])(?=[\s>])", lambda m: m.group(1) + str(int(m.group(2)) + 1), body_html)


KATEX_HEAD_EXTRA = (
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">\n'
    '  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>\n'
    '  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>\n'
    '  <script>'
    'document.addEventListener("DOMContentLoaded", function () {'
    'try { renderMathInElement(document.querySelector(".essay-body"), {'
    'delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }]'
    '}); } catch (e) { /* KaTeX 加载失败时公式保持原文卡片 */ }'
    '});</script>'
)


def rewrite_anchors(body_html: str, stats: dict) -> str:
    """按任务规则改写相对链接。"""

    def repl(m: "re.Match[str]") -> str:
        href, text = m.group(1), m.group(2)
        # 网络链接 / 站内根绝对路径 / 锚点 / 邮箱, 原样保留
        if href.startswith(("http://", "https://", "/", "#", "mailto:")):
            return m.group(0)
        # 相对链接
        clean = href.split("#", 1)[0].split("?", 1)[0]
        basename = clean.rstrip("/").rsplit("/", 1)[-1]
        if basename in INTERNAL_LINK_MAP:
            stats["internal"] += 1
            return f'<a href="{INTERNAL_LINK_MAP[basename]}">{text}</a>'
        if basename.lower().endswith(LOCAL_EXTS):
            # 指向未上传的本地资料: 去掉 <a>, 保留文字并加后缀
            stats["stripped_local"] += 1
            return f"{text}（本地资料，未上传）"
        # 其余相对链接（如 $$ 公式被 markdown 误认成的 t-0）: 去掉 <a> 保留原文, 不加后缀
        stats["stripped_other"] += 1
        return text

    return ANCHOR_RE.sub(repl, body_html)


def render_toc(tokens: list, skip_name: str) -> str:
    """渲染目录卡片; 跳过与文档标题相同的首个一级标题。"""

    def render_token(tok: dict) -> str:
        children = "".join(render_token(c) for c in tok.get("children", []))
        child_html = f"<ul>{children}</ul>" if children else ""
        cls = ' class="toc-l1"' if tok["level"] == 1 else ""
        return (
            f'<li{cls}><a href="#{tok["id"]}">{html.escape(tok["name"])}</a>{child_html}</li>'
        )

    items = []
    for idx, tok in enumerate(tokens):
        if idx == 0 and tok.get("level") == 1 and tok.get("name") == skip_name:
            # 文档标题本身不进目录, 但其下级标题要提上来
            items.extend(tok.get("children", []))
            continue
        items.append(tok)
    if not items:
        return ""
    inner = "".join(render_token(t) for t in items)
    return (
        '<nav class="note-toc" aria-label="本页目录">'
        '<div class="note-toc-title" aria-hidden="true">📑 本页目录</div>'
        f"<ul>{inner}</ul></nav>"
    )


def build_one(note: dict, source_dir: Path, out_dir: Path, stats: dict) -> dict:
    src = source_dir / note["source"]
    text = src.read_text(encoding="utf-8")

    title = doc_title(text) or src.stem
    course = note["course"]
    slug = note["slug"]

    # 阅读时长: 正文字数(不含空白) / 400 向上取整, 按原始 md 统计
    chars = len(re.sub(r"\s+", "", text))
    minutes = max(1, math.ceil(chars / 400))

    text, math_stash = protect_math(text)

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "1-3"}},
    )
    body = md.convert(text)
    toc_html = render_toc(md.toc_tokens, title)

    body = restore_math(body, math_stash)
    body = demote_headings(body)
    body = rewrite_anchors(body, stats)

    head_extra = KATEX_HEAD_EXTRA if math_stash else ""
    page = PAGE_TEMPLATE
    for key, value in {
        "TITLE": html.escape(title),
        "COURSE": html.escape(course),
        "SLUG": slug,
        "MINUTES": str(minutes),
        "TOC": toc_html,
        "BODY": body,
        "HEAD_EXTRA": head_extra,
    }.items():
        page = page.replace("{{" + key + "}}", value)

    if "{{" in page:
        raise RuntimeError(f"{slug}: 页面模板有未替换的占位符")

    html_path = out_dir / f"{slug}.html"
    html_path.write_text(page, encoding="utf-8")
    md_path = out_dir / f"{slug}.md"
    shutil.copyfile(src, md_path)  # 原样拷贝, 供"下载 Markdown"

    return {"html": html_path, "md": md_path, "minutes": minutes}


def main() -> int:
    parser = argparse.ArgumentParser(description="把复习笔记 md 转成站点页面")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="源 md 根目录")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出目录")
    args = parser.parse_args()

    source_dir = args.source.resolve()
    out_dir = args.out.resolve()

    for note in NOTES:
        if not (source_dir / note["source"]).is_file():
            print(f"[缺失] {source_dir / note['source']}", file=sys.stderr)
            return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"internal": 0, "stripped_local": 0, "stripped_other": 0}
    for note in NOTES:
        result = build_one(note, source_dir, out_dir, stats)
        print(
            f"[OK] {note['source']} -> {result['html'].relative_to(REPO_ROOT)} "
            f"({result['html'].stat().st_size} B) + {result['md'].relative_to(REPO_ROOT)} "
            f"({result['md'].stat().st_size} B) | 阅读约 {result['minutes']} 分钟"
        )

    print(
        f"链接改写: 站内跳转 {stats['internal']} 处, "
        f"去链接(本地资料) {stats['stripped_local']} 处, "
        f"去链接(其他相对路径/公式误判) {stats['stripped_other']} 处"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
