"""Knowledge Publisher 核心管线测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ast_nodes import CodeBlock, Heading, MathBlock, Table  # noqa: E402
from src.paginator import paginate  # noqa: E402
from src.parser import parse  # noqa: E402
from src.renderer.douyin import DouyinRenderer  # noqa: E402
from src.renderer.douyin_article import DouyinArticleRenderer  # noqa: E402
from src.renderer.zhihu import to_markdown  # noqa: E402
from src.validator import check_article  # noqa: E402
from src.templates import load_project_config  # noqa: E402

SAMPLE = ROOT / "articles" / "math" / "gradient-descent.md"


def _doc():
    return parse(SAMPLE.read_text(encoding="utf-8"))


def test_parse_structure():
    doc, meta = _doc()
    kinds = {type(b) for b in doc.children}
    assert Heading in kinds and MathBlock in kinds and CodeBlock in kinds and Table in kinds
    assert meta["title"] == "梯度下降到底是什么？"
    # H1 不进入正文分页
    assert doc.children[0].level == 1


def test_inline_math():
    doc, _ = _doc()
    found = False
    for h in doc.children:
        if isinstance(h, Heading) and "核心思想" in str(h.children):
            found = True
    assert found


def test_zhihu_roundtrip():
    doc, _ = _doc()
    md = to_markdown(doc)
    assert "$$" in md
    assert "```python" in md
    assert "![梯度下降示意图](assets/images/gradient.png)" in md


def test_pagination():
    doc, meta = _doc()
    renderer = DouyinRenderer(ROOT, ROOT / "output" / "_test")
    pages, outline = paginate(doc, meta, renderer)
    assert pages[0].kind == "cover"
    assert pages[-1].kind == "summary"
    assert len(pages) >= 3
    assert outline and outline[0]["page"] >= 1


def test_check_passes():
    cfg = load_project_config(ROOT)
    report = check_article(SAMPLE, ROOT, cfg)
    assert not report.errors, report.errors
    assert report.stats["formulas"] >= 4


def test_douyin_article_no_latex():
    """抖音长文：公式必须转成图片，输出里不能残留 $。"""
    result = DouyinArticleRenderer(ROOT, ROOT / "output" / "_test").build(SAMPLE)
    md = result["md"].read_text(encoding="utf-8")
    html = result["html"].read_text(encoding="utf-8")
    assert "$" not in md
    assert "$" not in html
    assert "![公式" in md
    assert "data:image/png;base64" in html
    formula_files = list(result["formulas"].glob("*.png"))
    assert len(formula_files) >= 4


def test_import_article():
    """导入功能：写入分类目录、重名报错、文件名净化。"""
    from src.cli import save_imported_article

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        target = save_imported_article(root, "梯度下降笔记", "math",
                                       "# 测试\n\n内容")
        assert target.exists()
        assert target.parent.name == "math"
        assert target.read_text(encoding="utf-8").startswith("# 测试")
        try:
            save_imported_article(root, "梯度下降笔记", "math", "x")
            assert False, "重名应报错"
        except ValueError:
            pass
        # 非法字符净化
        t2 = save_imported_article(root, 'a/b:c*?', "math", "x")
        assert "/" not in t2.stem and "*" not in t2.stem and "?" not in t2.stem
