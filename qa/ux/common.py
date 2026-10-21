"""Shared helpers for the WeddingAI.video UX / interaction test harness.

Target under test: local `wrangler pages dev` on 127.0.0.1:8788 (production-parity:
functions/_middleware.js i18n rewrite, CSP nonce, _redirects, _headers all run).

Design notes
------------
* Third-party origins (GA4 / Clarity / Baidu / AdSense) are blocked at the route
  layer so runs are deterministic and offline-safe. Blocked requests are counted
  separately and never counted as product defects.
* Service workers are blocked (`service_workers="block"`) so the SW cache from an
  earlier visit cannot mask or fake results.
* The cookie banner is auto-dismissed in the sweep (it would otherwise cover the
  viewport and shift layout) but its presence is recorded; the interaction suite
  tests it explicitly.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin

BASE = os.environ.get("UX_BASE", "http://127.0.0.1:8788")
ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"
SHOTS = RESULTS / "shots"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},   # iPhone 14
    "tablet": {"width": 768, "height": 1024},   # iPad portrait
    "desktop": {"width": 1440, "height": 900},
}

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

# Expected dominant script per language (for the "did the i18n layer actually
# translate this?" heuristic).
LANG_SCRIPT = {
    "en": "latin", "es": "latin", "fr": "latin", "de": "latin", "pt": "latin",
    "ru": "cyrillic", "zh": "cjk", "ja": "kana", "ar": "arabic",
    "hi": "devanagari", "th": "thai",
}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")

PAGE_PROBE_JS = r"""
() => {
  const out = {};
  const de = document.documentElement;
  const vis = el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  /* ---------- horizontal overflow ---------- */
  out.scrollWidth = de.scrollWidth;
  out.clientWidth = de.clientWidth;
  out.overflowX = Math.max(0, de.scrollWidth - de.clientWidth);
  out.overflowOffenders = [];
  if (out.overflowX > 2) {
    const vw = de.clientWidth;
    const bad = [];
    const all = document.body ? document.body.querySelectorAll('*') : [];
    for (let i = 0; i < all.length && bad.length < 400; i++) {
      const el = all[i];
      if (!vis(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.position === 'fixed') continue;
      const r = el.getBoundingClientRect();
      if (r.right > vw + 2 || r.left < -2) {
        bad.push({
          tag: el.tagName.toLowerCase(),
          cls: (typeof el.className === 'string' ? el.className : '').slice(0, 70),
          id: el.id || '',
          left: Math.round(r.left),
          right: Math.round(r.right),
          w: Math.round(r.width),
          depth: (function () { let d = 0, p = el; while ((p = p.parentElement)) d++; return d; })(),
        });
      }
    }
    // shallowest offenders are the ones actually causing the overflow
    bad.sort((a, b) => a.depth - b.depth || (b.right - b.left) - (a.right - a.left));
    out.overflowOffenders = bad.slice(0, 6);
  }

  /* ---------- headings ---------- */
  const heads = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'));
  out.h1 = heads.filter(h => h.tagName === 'H1').map(h => (h.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 110));
  out.headingOrder = heads.map(h => Number(h.tagName[1]));
  out.headingCounts = {};
  heads.forEach(h => { const t = h.tagName; out.headingCounts[t] = (out.headingCounts[t] || 0) + 1; });

  /* ---------- duplicate ids ---------- */
  const idMap = {};
  document.querySelectorAll('[id]').forEach(el => { idMap[el.id] = (idMap[el.id] || 0) + 1; });
  out.dupIds = Object.keys(idMap).filter(k => idMap[k] > 1).slice(0, 12);

  /* ---------- images ---------- */
  const imgs = Array.from(document.images);
  out.imgTotal = imgs.length;
  out.imgNoAlt = imgs.filter(i => !i.hasAttribute('alt')).slice(0, 6)
    .map(i => (i.currentSrc || i.src || '(no src)').split('/').slice(-1)[0]);
  out.imgNoAltCount = imgs.filter(i => !i.hasAttribute('alt')).length;
  const vh = window.innerHeight;
  out.brokenImages = imgs.filter(i => {
    const r = i.getBoundingClientRect();
    const inView = r.top < vh * 2 && r.bottom > -vh && r.width > 0;
    return inView && i.complete && i.naturalWidth === 0;
  }).slice(0, 8).map(i => (i.currentSrc || i.src || '').split('/').slice(-1)[0]);

  /* ---------- accessible names on controls ---------- */
  const accName = el => {
    const aria = el.getAttribute('aria-label');
    if (aria && aria.trim()) return aria.trim();
    const lb = el.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\s+/).map(id => (document.getElementById(id) || {}).textContent || '').join(' ').trim();
      if (t) return t;
    }
    const txt = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (txt) return txt;
    const title = el.getAttribute('title');
    if (title && title.trim()) return title.trim();
    const img = el.querySelector('img[alt]');
    if (img && img.getAttribute('alt').trim()) return img.getAttribute('alt').trim();
    const svg = el.querySelector('svg title');
    if (svg) return (svg.textContent || '').trim();
    const val = el.getAttribute('value');
    if (val && val.trim()) return val.trim();
    return '';
  };
  const ctrls = Array.from(document.querySelectorAll('a[href], button, [role="button"], input[type="submit"], input[type="button"]'));
  out.ctrlTotal = ctrls.length;
  out.unnamedCtrls = ctrls.filter(el => vis(el) && !accName(el)).slice(0, 8).map(el => ({
    tag: el.tagName.toLowerCase(),
    cls: (typeof el.className === 'string' ? el.className : '').slice(0, 60),
    href: (el.getAttribute('href') || '').slice(0, 60),
  }));
  out.unnamedCtrlsCount = ctrls.filter(el => vis(el) && !accName(el)).length;

  /* ---------- tap targets (WCAG 2.2 AA 24x24 CSS px minimum) ----------
     WCAG 2.2 "Target Size (Minimum)" exempts targets that sit inline inside a
     sentence, so inline links inside text flow are not counted; standalone
     buttons / icon buttons / nav links are. */
  let tiny24 = 0, tiny44 = 0;
  const tinySamples = [];
  const inTextFlow = el => {
    let p = el;
    while (p && p !== document.body) {
      const cs = getComputedStyle(p);
      if (cs.display !== 'inline') return false;
      p = p.parentElement;
      if (p && ['P', 'LI', 'TD', 'TH', 'SPAN', 'FIGCAPTION', 'BLOCKQUOTE', 'DD', 'DT', 'LABEL', 'BUTTON'].includes(p.tagName)) return true;
      if (p) { const pcs = getComputedStyle(p); if (pcs.display !== 'inline' && p.tagName !== 'A' && p.tagName !== 'SPAN') return false; }
    }
    return false;
  };
  ctrls.forEach(el => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    const w = Math.round(r.width), h = Math.round(r.height);
    if (w === 0 || h === 0) return;
    const isLink = el.tagName === 'A';
    if (isLink && getComputedStyle(el).display === 'inline' && inTextFlow(el)) return;
    if (w < 24 || h < 24) {
      tiny24++;
      if (tinySamples.length < 8) tinySamples.push({ tag: el.tagName.toLowerCase(), cls: (typeof el.className === 'string' ? el.className : '').slice(0, 50), w, h, text: accName(el).slice(0, 30), href: (el.getAttribute('href') || '').slice(0, 40) });
    } else if (w < 44 || h < 44) tiny44++;
  });
  out.tiny24 = tiny24; out.tiny24Samples = tinySamples; out.tiny44 = tiny44;

  /* ---------- form fields ---------- */
  const fields = Array.from(document.querySelectorAll('input, select, textarea'))
    .filter(el => {
      const t = (el.type || '').toLowerCase();
      return !['hidden', 'submit', 'button', 'reset', 'image'].includes(t);
    });
  out.fieldTotal = fields.length;
  const unlabeled = fields.filter(el => {
    if (!vis(el)) return false;               // hidden honeypots are not AT-exposed
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return false;
    if (el.id && document.querySelector('label[for="' + CSS.escape(el.id) + '"]')) return false;
    if (el.closest('label')) return false;
    return true;
  });
  out.unlabeledFields = unlabeled.slice(0, 8).map(el => ({
    tag: el.tagName.toLowerCase(), type: el.type || '', name: el.name || '', id: el.id || '',
  }));
  out.unlabeledFieldsCount = unlabeled.length;

  /* CSS-hidden file inputs: not focusable, not announced, keyboard users cannot
     open a file picker unless some other control proxies it. */
  out.hiddenFileInputs = Array.from(document.querySelectorAll('input[type="file"]'))
    .filter(i => !vis(i))
    .map(i => ({
      id: i.id || '',
      labelled: !!(i.id && document.querySelector('label[for="' + CSS.escape(i.id) + '"]')) || !!i.closest('label'),
      proxyFocusable: !!document.querySelector(
        '[id*="dropzone"][tabindex], [class*="dropzone"][tabindex], label[for="' + (i.id || 'x') + '"], button[aria-controls*="' + (i.id || 'x') + '"]'),
    }));
  out.hiddenFileInputCount = out.hiddenFileInputs.length;

  /* ---------- document meta ---------- */
  out.htmlLang = de.getAttribute('lang') || '';
  const vp = document.querySelector('meta[name="viewport"]');
  out.viewportMeta = vp ? vp.getAttribute('content') : '';
  out.title = (document.title || '').trim();
  out.canonical = (document.querySelector('link[rel="canonical"]') || {}).href || '';
  out.metaDesc = ((document.querySelector('meta[name="description"]') || {}).content || '').trim();

  /* ---------- script composition of visible text ---------- */
  const txt = (document.body ? (document.body.innerText || '') : '').slice(0, 200000);
  out.textLen = txt.length;
  const counts = {
    latin: (txt.match(/[A-Za-z]/g) || []).length,
    cjk: (txt.match(/[\u4e00-\u9fff]/g) || []).length,
    kana: (txt.match(/[\u3040-\u30ff]/g) || []).length,
    cyrillic: (txt.match(/[\u0400-\u04ff]/g) || []).length,
    arabic: (txt.match(/[\u0600-\u06ff]/g) || []).length,
    devanagari: (txt.match(/[\u0900-\u097f]/g) || []).length,
    thai: (txt.match(/[\u0e00-\u0e7f]/g) || []).length,
  };
  out.scripts = counts;
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  out.latinRatio = total ? +(counts.latin / total).toFixed(3) : 0;
  let dom = null, domV = -1;
  for (const k of Object.keys(counts)) { if (counts[k] > domV) { domV = counts[k]; dom = k; } }
  out.dominantScript = dom;

  /* ---------- links ---------- */
  const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href'));
  out.linkTotal = links.length;
  const internal = new Set(), external = new Set();
  links.forEach(h => {
    if (!h) return;
    if (/^(mailto:|tel:|javascript:|#|data:)/i.test(h)) return;
    if (/^https?:\/\//i.test(h)) {
      if (h.startsWith(location.origin)) internal.add(h);
      else external.add(h.split('?')[0]);
    } else if (h.startsWith('/')) internal.add(h.split('#')[0].split('?')[0]);
    else internal.add(h.split('#')[0].split('?')[0]);
  });
  out.internalLinks = Array.from(internal);
  out.externalHosts = Array.from(new Set(Array.from(external).map(u => { try { return new URL(u).host; } catch (e) { return u; } })));

  /* ---------- in-page anchors ---------- */
  const hashLinks = links.filter(h => h && h.startsWith('#') && h.length > 1);
  out.deadAnchors = hashLinks.filter(h => !document.getElementById(h.slice(1))).slice(0, 10);

  /* ---------- interactive widgets present ---------- */
  out.widgets = {
    mobileMenuToggle: !!document.querySelector('.mobile-menu-toggle'),
    mainNav: !!document.querySelector('.main-nav'),
    langSelect: !!document.querySelector('#wa-lang-select'),
    faqDetails: document.querySelectorAll('details').length,
    forms: document.querySelectorAll('form').length,
    fileInputs: document.querySelectorAll('input[type="file"]').length,
    canvas: document.querySelectorAll('canvas').length,
    videos: document.querySelectorAll('video').length,
    filterBtns: document.querySelectorAll('.filter-btn').length,
    tables: document.querySelectorAll('table').length,
  };

  /* ---------- perf snapshot ---------- */
  const nav = performance.getEntriesByType('navigation')[0];
  if (nav) {
    out.dcl = Math.round(nav.domContentLoadedEventEnd);
    out.load = Math.round(nav.loadEventEnd);
  }
  let bytes = 0, reqs = 0;
  performance.getEntriesByType('resource').forEach(r => { bytes += (r.transferSize || 0); reqs++; });
  out.transferKB = Math.round(bytes / 1024);
  out.reqCount = reqs;
  out.domNodes = document.querySelectorAll('*').length;

  return out;
}
"""


# --------------------------------------------------------------------------- #
# URL inventory
# --------------------------------------------------------------------------- #

def sitemap_urls(name: str) -> list[str]:
    """Local paths from sitemap-<name>.xml (prod URLs rewritten to site root)."""
    f = ROOT / f"sitemap-{name}.xml"
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in re.findall(r"<loc>(.*?)</loc>", text):
        p = urlparse(m).path or "/"
        if not p.endswith("/") and "." not in p.split("/")[-1]:
            p += "/"
        out.append(p)
    return out


def to_local(path: str) -> str:
    return BASE + path


def lang_of(path: str) -> str:
    m = re.match(r"^/([a-z]{2})/", path)
    return m.group(1) if m else "en"


def en_urls() -> list[str]:
    return sitemap_urls("en")


def archetype_paths(lang: str = "en") -> list[str]:
    """One representative page per page archetype, for a given language."""
    prefix = "" if lang == "en" else f"/{lang}"
    slugs = [
        f"{prefix}/",
        f"{prefix}/pricing/",
        f"{prefix}/tools/",
        f"{prefix}/tools/wedding-hashtag-generator/",
        f"{prefix}/tools/compress-wedding-photos/",
        f"{prefix}/gallery/",
        f"{prefix}/order/",
        f"{prefix}/blog/",
        f"{prefix}/services/",
        f"{prefix}/about/",
        f"{prefix}/resources/",
        f"{prefix}/success/",
        f"{prefix}/ai-wedding-video-generator/",
    ]
    return slugs


def blog_article_path(lang: str = "en", idx: int = 0) -> str:
    prefix = "" if lang == "en" else f"/{lang}"
    arts = [p for p in sitemap_urls(lang) if p.startswith(f"{prefix}/blog/") and p.rstrip("/") != f"{prefix}/blog"]
    if not arts:
        return f"{prefix}/blog/"
    return arts[idx % len(arts)]


# --------------------------------------------------------------------------- #
# Result IO
# --------------------------------------------------------------------------- #

def save(name: str, data) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return p


def load(name: str):
    p = RESULTS / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def slugify(path: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-")
    return (s or "root")[:80]
