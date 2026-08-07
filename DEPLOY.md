# WeddingAI.video — Deploy Workflow

How a code change goes from your dev box to https://weddingai.video. Read this
before pushing anything.

> **Deployment tool: `git push` only.** `wrangler pages deploy` CLI is **deprecated**
> for this project (set 2026-08-07). Always ship via `git push origin main`; CF Pages
> auto-builds from the GitHub integration. `wrangler.toml` stays in the repo for KV
> bindings + function config — it is not a deploy entry point. `scripts/deploy.ps1`
> (the wrangler wrapper) is kept for legacy reference but should not be used.

## TL;DR

```
本地改代码 → 本地 pre-deploy 跑通 → git push origin main (SSH)
  → GitHub Actions: pre-deploy (主门禁) + ci/validate (supplementary)
    → Cloudflare Pages: 自动 build + deploy
      → 生产 https://weddingai.video 更新
```

平均 push-to-prod 时间：50–80s（pre-deploy 50s + CF Pages 5–30s）。

---

## 1. 本地开发

### 仓库位置
```
C:\Users\qiaoshan\.openclaw\workspace\weddingai
```

### 分支约定
- **`main`** — 生产分支。Default branch on GitHub。**唯一 push 到 remote 的分支。**
- **`dev`**（local-only）— 你个人 WIP 用，**永远不 push**。日常 `git checkout dev` 切过去改东西，测完 `git checkout main && git merge dev` 再 push。

```bash
# 日常本地循环
git checkout dev
# ... 改东西 ...
.\internal-tools\pre-deploy-check.ps1    # 跑全量本地检查
git add -A
git commit -m "..."
git checkout main
git merge --ff-only dev
git push origin main
```

### 本地 pre-deploy
**这一个脚本 = CI 主门禁跑的那一个**。本地过 = CI 必过。

```powershell
cd C:\Users\qiaoshan\.openclaw\workspace\weddingai
.\internal-tools\pre-deploy-check.ps1
```

期望输出末尾：
```
Errors:   0
Warnings: 1
READY TO DEPLOY
```

> 1 个 warning (`GA4 found in 527/528 pages`) 是 pre-existing 基线，不需要修。
> 任何 `Errors: N`（N>0）= **不要 push**，先 fix。

### 一次性环境检查（确认机器就绪）
- Python 在 PATH（`python --version` 应该有 3.x）
- `git` 在 PATH
- SSH key `~/.ssh/id_ed25519` 存在（`Test-Path ~/.ssh/id_ed25519`）
- `~/.ssh/config` 里有 `Host github.com` 配 `IdentityFile ~/.ssh/id_ed25519`

---

## 2. 推送

```bash
git push origin main
```

**不要用 PAT**。GitHub fine-grained PAT 会被 anomaly detection 自动 revoke。SSH key 是唯一可靠的方式。

```bash
# 验证 SSH 通了
ssh -T git@github.com
# 应该输出: Hi jack-joe-ai! You've successfully authenticated...
```

### 大文件
视频资源走 Git LFS。`.gitattributes` 已配：
```
*.mp4 / *.webm / *.mov / *.avi / *.mkv  filter=lfs diff=lfs merge=lfs -text
```

普通 `git push` 会自动传 LFS 对象，不用手动操作。

---

## 3. GitHub Actions 流程

push 到 `main` 触发 **2 个 workflow 并行**。

### 3a. `pre-deploy.yml` — **主门禁**（必过）

- **Runner**: `windows-latest`
- **耗时**: 50–60s
- **步骤**:
  1. `actions/checkout@v4` (with LFS)
  2. `actions/setup-python@v5` (3.11)
  3. **Force UTF-8 I/O** (`PYTHONIOENCODING=utf-8` env var) — Windows cp1252 会让 ✅/❌/→/⚠️ emoji 崩
  4. Run `internal-tools\pre-deploy-check.ps1` — 25 个 PowerShell 检查（CSP nonces, hN tag mismatch, inline event handlers, GA4 ID, CF Functions, relative `<script src>`, CSS empty rules, critical files, secrets in `functions/`, etc.）
  5. Run `qa/full_qa.py` — Python i18n + structural

- **结果**:
  - ✅ green → CI 端认为代码可部署
  - ❌ red → 修代码再 push。**不要 force-push 跳过**

### 3b. `ci.yml` — **Supplementary check**（建议过）

- **Runner**: `ubuntu-latest`
- **耗时**: 15–25s
- **步骤**:
  1. Secret scan（grep `re_/sk-/ghp_/AIza/AKIA` patterns）
  2. `.assetsignore` 必备 pattern check
  3. `python scripts/check_langs_sync.py`
  4. `_redirects` 必备 404 rules check
  5. `sitemap.xml` 包含今天的 `<lastmod>`
  6. `python qa/verify_sitemap.py`（fetch 一个 hardcoded preview URL 验证）

- **结果**:
  - ✅ green → 干净
  - ❌ red → **不挡 CF Pages 部署**，但应当尽快修（见下方"已知 brittle 点"）

---

## 4. Cloudflare Pages 自动部署

dashboard 已配：
- Project: `weddingai-video`
- Build command: 空（静态站）
- Build output: `/`
- Production branch: `main`
- Preview branch: ~~dev~~（已删除，local-only）
- **Production branch control**: 建议勾上 → pre-deploy 不绿就 block 部署

每次 push 到 main，CF Pages 会自动 build + deploy 到 `https://weddingai.video`。

预览（PR 类的）目前没配（因为 dev 是 local-only，没法自动开 preview URL）。

---

## 5. 完整 push checklist

每次 push 前：

- [ ] 本地 `.\internal-tools\pre-deploy-check.ps1` = 0 errors
- [ ] `git status` 干净，没有意外文件
- [ ] 改了 `sitemap.xml`？重新生成过 `python qa/gen_sitemap.py`？
- [ ] 加了新的内部文件？同时加到 `_redirects` 404 + `ci.yml` 的 path list
- [ ] 改了 Python 脚本？检查 import 顺序（`from __future__` 必须在最前）

---

## 6. 已知 brittle 点（踩过的坑）

### 6.1 `ci.yml` hardcode 8 个 404 路径
文件 `ci.yml` 第 60 行：
```bash
for path in /AGENTS.md /CHANGELOG.md /README.md /_headers.bak /scripts/ /qa/ /tmp/ /netlify.toml; do
```
加新内部文件要**同时**改 `_redirects` 和这个 list。忘了 ci/validate fail 19s。

**长期修复**：用 `find . -maxdepth 1 -type f \( -name "*.md" -o -name "*.py" -o -name "*.toml" \)` 自动发现。

### 6.2 Secret regex 太松
`ci.yml` 第 31 行的 regex：
```
re_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|...
```
真实 Resend API key 是 `re_` + **32** 字符。20 字符门槛太松，会误伤 i18n key 文本（French 博客有个 key 是 `intgration_de_votre_animal` + `servicespersonalization` 拼一起，31 字符正好触发）。

**长期修复**：收紧到 `re_[A-Za-z0-9]{32,}` / `sk-[A-Za-z0-9]{48,}`。

### 6.3 sitemap lastmod strict today
`ci.yml` 第 74-79 行要求 `<lastmod>YYYY-MM-DD</lastmod>` 是今天。明天再 push 就 fail。

**长期修复**：改成 `<lastmod>${7 days ago}</lastmod>` 或 `<lastmod>${today}</lastmod>`，7 天内都算合格。或者改 `gen_sitemap.py` 强制所有 lastmod 用 today（牺牲 mtime 精度但永远过 CI）。

### 6.4 `_redirects` 缺 `/_headers.bak` 404 规则
历史上一直缺，但 `ci.yml` 检查 19s fail 又没挡 deploy（pre-deploy + CF Pages deploy 都还成功），所以**长期 silent fail**。最近才被发现。

**症状**：看 Actions tab，`CI / validate` 一直 ❌ 但 `Pre-Deploy Check` + `Cloudflare Pages` 都 ✅。

**修复**：往 `_redirects` 加 `/_headers.bak  /404  404`。

---

## 7. 紧急情况

### Rollback 一次 deploy
```bash
# 找到上一个 green main commit
git log --oneline main -10
# 假设上一个好的 commit 是 abc1234
git checkout main
git revert --no-edit abc1234    # 创建新 commit 反向，不动 history
git push origin main
```

CF Pages 会自动 deploy revert 的版本。

### SSH 失效 / key 失效
1. 新生成 key: `ssh-keygen -t ed25519 -C "reup.shan@gmail.com" -f ~/.ssh/id_ed25519`
2. 把 `~/.ssh/id_ed25519.pub` 内容加到 https://github.com/settings/keys
3. `~/.ssh/config` 里 `Host github.com` 配 `IdentityFile ~/.ssh/id_ed25519`
4. `ssh -T git@github.com` 验证

### 本地 pre-deploy 通过但 CI 失败
几乎一定是以下之一：
1. **cp1252 unicode error** — Python 脚本打印非 ASCII 没 reconfigure。加 `sys.stdout.reconfigure(encoding="utf-8")` 到脚本顶部，或在 workflow 设 `PYTHONIOENCODING=utf-8`
2. **缺 `from pathlib import Path` import** — rewriter 把 `ROOT = r"..."` (string) 改成了 `ROOT = Path(...)` 但没补 import
3. **硬编码路径** — 任何 `C:\Users\qiaoshan\...` 引用都会让 CI 找不到文件

---

## 8. 相关文件

| 文件 | 作用 |
|------|------|
| `.github/workflows/pre-deploy.yml` | 主门禁 workflow |
| `.github/workflows/ci.yml` | Supplementary check workflow |
| `internal-tools/pre-deploy-check.ps1` | 25 个 PowerShell check |
| `qa/full_qa.py` | Python i18n / structural check |
| `qa/gen_sitemap.py` | 生成 sitemap |
| `qa/verify_sitemap.py` | 验证 sitemap (fetch preview URL) |
| `qa/check_blog_redirects.py` | Blog 50 条 301 retention check |
| `scripts/check-seo-lengths.py` | Title/description length check |
| `scripts/check_langs_sync.py` | Lang list consistency check |
| `_redirects` | CF Pages redirect rules（含 404 内部文件） |
| `sitemap.xml` + `sitemap-*.xml` | 10 语言 sitemap |
| `wrangler.toml` | CF Pages / Workers / KV 配置 |
| `.gitattributes` | LFS + line ending 规则 |
| `.gitignore` | local-only 文件排除 |
| `.assetsignore` | 部署时排除的内部文件 pattern |

---

## 9. 切勿做

- ❌ **`wrangler pages deploy`** — 已弃用。用 `git push origin main` 走 CF Pages GitHub 集成。
- ❌ **`git push origin dev`** — dev 已删除
- ❌ **Force-push main 跳过 pre-deploy** — 万一代码真有 bug，CF Pages branch control 会挡；没挡就会部署坏代码
- ❌ **改 `_redirects` 不更新 `ci.yml` path list** — ci/validate 会 fail（见 6.1）
- ❌ **直接 `git push` 大视频文件** — 必须通过 LFS（看 `.gitattributes`，已经配好了）
- ❌ **把 secret token 写到代码里** — `internal-tools/pre-deploy-check.ps1` 第 8 步会 grep 扫；CI 也会扫
- ❌ **commit `100 blog/` 那种 scratch dir** — 误提交垃圾会污染 repo
