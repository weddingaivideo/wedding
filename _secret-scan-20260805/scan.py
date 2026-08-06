import os, re, sys, json

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
GITIGNORE_PATH = os.path.join(ROOT, ".gitignore")

def load_gitignore():
    rules = []
    if not os.path.exists(GITIGNORE_PATH):
        return rules
    with open(GITIGNORE_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            pattern = line[1:] if negated else line
            # Convert simple glob to regex
            pattern = pattern.replace(".", r"\.").replace("*", "[^/]*").replace("?", "[^/]")
            rules.append((negated, pattern))
    return rules

def is_ignored(rel, rules):
    # Apply rules in order; later rules override earlier
    ignored = False
    for negated, pattern in rules:
        if re.search(pattern, rel) or re.search(pattern, "/" + rel):
            if negated:
                ignored = False
            else:
                ignored = True
    return ignored

rules = load_gitignore()
print(f"Loaded {len(rules)} .gitignore rules")

SCAN_PATTERNS = [
    (r"gh[pousr]_[A-Za-z0-9]{36,}\b", "high", "GitHub PAT (ghp_/ghs_/gho_/ghu_/ghr_)"),
    (r"github_pat_[A-Za-z0-9_]{60,}\b", "high", "GitHub fine-grained PAT (github_pat_)"),
    (r"\bsk_live_[A-Za-z0-9]{20,}\b", "high", "Stripe live secret key"),
    (r"\brk_live_[A-Za-z0-9]{20,}\b", "high", "Stripe live restricted key"),
    (r"\bre_[A-Za-z0-9]{20,}\b", "high", "Resend API key"),
    (r"\bSG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b", "high", "SendGrid API key"),
    (r"Bearer\s+[A-Za-z0-9_\-\.]{30,}", "medium", "Bearer token"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "medium", "JWT token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "high", "AWS access key"),
    (r"aws_secret_access_key\s*=\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", "high", "AWS secret access key"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----", "high", "Private key block"),
    (r"\bRESEND_API_KEY\s*=\s*['\"]?re_[A-Za-z0-9]{20,}", "high", "RESEND_API_KEY env var"),
    (r"\b[a-f0-9]{40}\b", "medium", "40-char hex (CF token candidate)"),
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([A-Za-z0-9!@#$%^&*]{12,})['\"]?", "low", "Password-like assignment"),
]

TEXT_EXT = {".html",".htm",".css",".js",".mjs",".cjs",".json",".md",".txt",".py",".sh",".ps1",".toml",".yml",".yaml",".xml",".svg",".env",".gitignore",".gitattributes",".lock",".ts",".tsx",".jsx",".csv",".log",".ini",".conf",".config",".example",".sample"}
BIN_EXT_TO_SKIP = {".mp4",".webm",".mp3",".wav",".png",".jpg",".jpeg",".gif",".webp",".avif",".pdf",".zip",".gz",".tar",".woff",".woff2",".ttf",".eot",".ico",".cur"}

# Safe file patterns (high false-positive rate)
SAFE_FILE_PATTERNS = [
    r"i18n/.+\.json$",
    r".+\.min\.(css|js)$",
    r"/sitemap.*\.xml$",
]

findings = {}
files_scanned = 0

for dirpath, dirnames, filenames in os.walk(ROOT):
    rel_dir = os.path.relpath(dirpath, ROOT)
    if is_ignored(rel_dir + "/" if rel_dir != "." else "", rules):
        dirnames[:] = []
        continue
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        if is_ignored(rel, rules):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext in BIN_EXT_TO_SKIP:
            continue
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (PermissionError, OSError):
            continue
        files_scanned += 1
        for pat, sev, label in SCAN_PATTERNS:
            for m in re.finditer(pat, content):
                val = m.group(0)
                if "EXAMPLE" in val or "PLACEHOLDER" in val or "xxxxx" in val.lower() or "your-key" in val.lower() or "<your" in val.lower():
                    continue
                if any(re.search(p, rel) for p in SAFE_FILE_PATTERNS):
                    continue
                findings.setdefault(rel, []).append({"severity": sev, "label": label, "match": val[:80]})

print(f"Scanned {files_scanned} text files (after .gitignore applied)")
total = sum(len(v) for v in findings.values())
high = sum(1 for fs in findings.values() for f in fs if f["severity"] == "high")
med = sum(1 for fs in findings.values() for f in fs if f["severity"] == "medium")
low = sum(1 for fs in findings.values() for f in fs if f["severity"] == "low")
print(f"Findings: {total} across {len(findings)} files")
print(f"  high:   {high}")
print(f"  medium: {med}")
print(f"  low:    {low}")
print("---")
for f, fs in sorted(findings.items()):
    for fnd in fs[:2]:
        print(f"  [{fnd['severity']:6s}] {fnd['label']:35s} in {f}")
        print(f"           match: {fnd['match']}")
    if len(fs) > 2:
        print(f"           ... and {len(fs)-2} more in this file")
