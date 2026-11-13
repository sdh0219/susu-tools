"""静态站点体检：检查 web/ 下所有 HTML 的本地 href/src 引用是否存在。

用法：python scripts/check_site.py
退出码：0 = 全部引用可达；1 = 存在失效引用（逐条打印）。
规则：
- 跳过 http(s):、mailto:、data:、纯锚点
- 以 / 开头的路径相对 web/ 解析；相对路径相对当前页面所在目录解析
- 带 #fragment 的站内 .html 链接同时校验目标页里存在该 id
- <script> 块整体跳过：JS 模板字符串里的 href/src 是运行时插值，不是静态链接
"""
import os
import re
import sys

root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
REF_RE = re.compile(r'(?:href|src)="([^"]+)"')
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
ID_RE = re.compile(r'id="([^"]+)"')
SKIP_PREFIX = ("http://", "https://", "mailto:", "data:", "tel:", "javascript:")

broken = []
checked = 0
target_ids = {}  # 目标页 id 集合缓存：锚点要拿目标页的 id 校验，不是当前页的


def page_ids(path):
    """读取一个 HTML 页面的全部 id（带缓存）。"""
    key = path.replace("\\", "/")
    if key not in target_ids:
        try:
            target_ids[key] = set(ID_RE.findall(open(path, encoding="utf-8", errors="ignore").read()))
        except OSError:
            target_ids[key] = set()
    return target_ids[key]


for dirpath, _dirnames, filenames in os.walk(root):
    for fn in sorted(filenames):
        if not fn.endswith(".html"):
            continue
        page = os.path.join(dirpath, fn).replace("\\", "/")
        rel = os.path.relpath(page, root).replace("\\", "/")
        try:
            text = open(page, encoding="utf-8", errors="ignore").read()
            text = SCRIPT_RE.sub("", text)  # 先剥离 <script>，避免把 JS 模板字符串当静态链接
        except OSError as exc:
            broken.append(f"{rel} :: 无法读取 ({exc})")
            continue
        for match in REF_RE.finditer(text):
            url = match.group(1)
            if url.startswith(SKIP_PREFIX):
                continue
            path, _, frag = url.partition("#")
            if not path:
                continue  # 纯锚点，只跳转本页
            if url.startswith("/"):
                target = os.path.join(root, path.lstrip("/"))
                target_rel = path.lstrip("/")
            else:
                target = os.path.normpath(os.path.join(dirpath, path))
                target_rel = os.path.relpath(target, root).replace("\\", "/")
            checked += 1
            if not os.path.exists(target):
                broken.append(f"{rel} -> {url}（文件不存在）")
                continue
            if frag and target_rel.endswith(".html") and os.path.isfile(target):
                if frag not in page_ids(target):
                    broken.append(f"{rel} -> {url}（目标页无 id=\"{frag}\"）")

if broken:
    print(f"BROKEN REFS: {len(broken)}")
    for line in broken:
        print(" ", line)
    sys.exit(1)

print(f"OK: {checked} local refs checked, all reachable")
sys.exit(0)
