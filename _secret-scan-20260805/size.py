import os, subprocess, re
ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
out = subprocess.check_output(["git", "-C", ROOT, "add", "-A", "-n"], text=True, errors="ignore")
files = []
for line in out.splitlines():
    m = re.match(r"^add ['\"](.+?)['\"]$", line)
    if m:
        files.append(m.group(1))
sized = []
for f in files:
    p = os.path.join(ROOT, f)
    if os.path.isfile(p):
        sized.append((f, os.path.getsize(p)))
sized.sort(key=lambda x: -x[1])
for f, sz in sized[:10]:
    print(f"  {sz:>10,}  {f}")
total = sum(s for _, s in sized)
print(f"\n  Total: {len(sized)} files, {total:,} bytes = {total/1024/1024:.2f} MB (before LFS)")
