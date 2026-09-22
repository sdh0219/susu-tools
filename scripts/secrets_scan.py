import os, re, subprocess

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True, encoding="utf-8").splitlines()
patterns = [
    ("sk-token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("gh-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("AKIA", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("privkey", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("SESSDATA", re.compile(r"SESSDATA[=:]\s*[^\s;,&\"']{10,}")),
    ("bili_jct", re.compile(r"bili_jct[=:]\s*[^\s;,&\"']{10,}")),
    ("Bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=|-]{25,}")),
    ("sk_live", re.compile(r"sk_live_[A-Za-z0-9]{10,}")),
    ("AIza", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("key_assign", re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*[\"']?(sk-|key-|gh[pousr]_)[A-Za-z0-9]{10,}")),
]
skip_ext = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".bin", ".woff", ".woff2", ".mp3", ".mp4", ".db", ".pack", ".idx", ".rev"}

hits = []
for f in tracked:
    ext = os.path.splitext(f)[1].lower()
    if ext in skip_ext:
        continue
    path = os.path.join(root, f)
    try:
        text = open(path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    for name, pat in patterns:
        if pat.search(text):
            hits.append(f"{f} :: {name}")

print("TRACKED_FILES", len(tracked))
if hits:
    print("HITS:")
    for h in hits:
        print(" ", h)
else:
    print("CLEAN: no high-confidence secret patterns in tracked files")

for p in ["cookies.txt", ".env", "_private_backup", "bili_note.db", "user_cookies"]:
    out = subprocess.check_output(["git", "log", "--all", "--oneline", "--", p], cwd=root, text=True, encoding="utf-8").strip()
    print("HISTORY", p, "=>", out if out else "clean")

p = os.path.join(root, "projects", "bilinote", ".env.example")
print("ENV_EXAMPLE:")
for line in open(p, encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    k, v = k.strip(), v.strip()
    if re.search(r"KEY|TOKEN|SECRET|PASSWORD|COOKIE", k, re.I):
        print(f"  {k}=<{'empty' if not v else 'redacted len=' + str(len(v))}>")
    else:
        print(f"  {k}={v}")
