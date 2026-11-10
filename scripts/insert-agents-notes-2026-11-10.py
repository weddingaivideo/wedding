#!/usr/bin/env python3
"""Insert three AGENTS.md sections about the traps found on 2026-11-10.

Inserted BEFORE "## The 13 free tools:" so the section sits next to the
other i18n notes, and before the font section another session is appending
at the end of the file (their hunk starts at line 1948, so this position is
untouched by them).

Writes two artefacts:
  - tmp/agents-staged.md  = HEAD's AGENTS.md + the new sections  (to stage)
  - AGENTS.md             = the working-tree file + the new sections
so the other session's in-flight edits stay out of the commit and the
working tree keeps both changes.
"""
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AGENTS = REPO / "AGENTS.md"
ANCHOR = "## The 13 free tools: what they really are, and the library shortlist (2026-11-09)"

SECTIONS = """## A `data-i18n` key resolves only if its NAMESPACE exists (2026-11-10)

**A key is not a key - it is a file.** The middleware files every key under
its **first two dotted segments** (`namespaceOf()` in
`functions/_lib/i18n-shards.js`): `blog.foo.bar.baz` -> namespace
`blog.foo`. The namespace is what the manifest maps to shard files.

A binding needs THREE things, and missing any one of them fails SILENTLY
(the page still returns 200, the translation is simply absent):

1. the key must exist in `i18n/<lang>.json`, or the element keeps its
   static source (`applyDataI18n()` does `if (v == null) return m`),
2. the namespace must be in `i18n/<lang>.manifest.json`, or no shard is
   ever fetched for it,
3. the namespace must exist as a shard file.

**The failure mode that hid for months.** A page was copy-pasted from a
sibling page and its `data-i18n` attributes were rewritten to a namespace
that exists NOWHERE:
`blog.include_remote_family_wedding_video.serp_comparison.*` (underscores)
while every dictionary uses the hyphenated
`blog.include-remote-family-wedding-video.*`. The middleware filed it under
`blog.include_remote_family_wedding_video`, which is not in the manifest,
so no shard was fetched and all 51 elements stayed empty - 6 blank headers,
42 blank cells, an empty heading, in all 11 languages, with no error
anywhere.

**The rule:** a namespace name is part of the data contract. When a page is
copied, copy the `data-i18n` keys verbatim or repoint them at a namespace
that exists. After any rename, check it:

```powershell
python scripts/verify-i18n-shards.py
```

A page with no localized static file is served from the English source and
translated at runtime, so one fix reaches all 11 languages - but only for
those pages. 63 pages per language DO have a hand-written localized file,
and those can drift from the English source (the zh copy of
`blog/best-ai-wedding-video-tools-2026/` has no comparison table at all
while the English one does).

## The CI gate pointed at scripts that did not exist (2026-11-10)

Both GitHub Actions jobs were red on every push since `c7747902` - the
housekeeping commit that deleted 140 one-off QA scripts. The workflows were
never updated:

- `.github/workflows/ci.yml` ran `python qa/verify_sitemap.py` -> deleted,
- `.github/workflows/pre-deploy.yml` ran `python qa/full_qa.py` -> deleted.

Both steps died with "can't open file" (exit 1) before they checked
anything, and nobody noticed because the Cloudflare Pages deploy is a
separate workflow. The surviving production scripts are
`qa/{deploy,gen_sitemap,qa_full_recheck,validate-deploy,validate-sitemap}.py`.

**A deleted script and a workflow that calls it fail in exactly the same
way as a real regression.** Before blaming the change, find out WHICH step
failed: `git log --diff-filter=D -- <path>` says whether the script was
ever there.

`ci.yml` also requires `sitemap.xml` to carry today's (UTC) lastmod, so
every push needs the dates refreshed with
`python scripts/_refresh_sitemap_lastmod.py` (UTC, because the gate compares
against `date -u`, not local time).

## The scratch directory is `.tmp`, not `tmp` (2026-11-10)

`.tmp/` holds ~1,400 backup / one-off HTML files and is gitignored, but the
scripts that walk the tree excluded `tmp` - not `.tmp` - so the scratch
files were counted as site pages:

- `qa/gen_sitemap.py` would have published internal URLs to search engines,
- `qa/full_qa.py` scanned 2,142 files instead of 721 and reported 13,358
  broken hrefs that live in scratch files (CI checks out a clean tree, so
  the two numbers were never comparable).

**A directory whose name starts with a dot is a DIFFERENT directory from
the one without it** - the same trap as `tmp/` vs `.tmp/` documented in
`.assetsignore`. Exclude both.

## The shard builder is not byte-deterministic (2026-11-10)

`qa/build-i18n-shards.py` emits the JSON keys in a different order on every
run (Python's per-process string-hash randomisation), so a rebuild always
shows the 11 blog-hub bundles and the manifests as changed even when
nothing moved. The gate compares SEMANTICALLY ("the shards merged back
equal the dictionary exactly"), so the churn is harmless - but do not
commit it: `git checkout` the bundles and manifests and keep only the
shards whose CONTENT actually changed.

"""


def insert(text: str) -> str:
    if ANCHOR not in text:
        raise RuntimeError("anchor heading not found")
    if "## A `data-i18n` key resolves only if its NAMESPACE exists" in text:
        return text
    return text.replace(ANCHOR, SECTIONS + ANCHOR, 1)


def main() -> int:
    head = subprocess.run(
        ["git", "show", "HEAD:AGENTS.md"], capture_output=True, cwd=str(REPO), check=True
    ).stdout.decode("utf-8")
    staged = insert(head)
    tmp = REPO / "tmp" / "agents-staged.md"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(staged, encoding="utf-8", newline="")
    sha = subprocess.run(
        ["git", "hash-object", "-w", str(tmp)], capture_output=True, text=True, cwd=str(REPO), check=True
    ).stdout.strip()
    mode = subprocess.run(
        ["git", "ls-files", "-s", "AGENTS.md"], capture_output=True, text=True, cwd=str(REPO)
    ).stdout.split()[0]
    subprocess.run(
        ["git", "update-index", "--add", "--cacheinfo", f"{mode},{sha},AGENTS.md"],
        check=True,
        cwd=str(REPO),
    )
    # Keep the working tree in sync (it also carries another session's edits).
    current = AGENTS.read_text(encoding="utf-8")
    updated = insert(current)
    if updated != current:
        AGENTS.write_text(updated, encoding="utf-8", newline="")
    print(f"staged blob {sha} (+{staged.count(chr(10)) - head.count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
