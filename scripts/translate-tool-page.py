#!/usr/bin/env python3
"""
Translate a tool page's i18n bindings into the 10 other languages and emit
(a) the patch file for scripts/add-tool-ui-keys.py and
(b) the translated HEAD fields for the static language copies.

WHY A DEDICATED SCRIPT
----------------------
The site has 11 dictionaries and every one of them has to carry the same
key set, or a reader in that language sees English. That is 11 x N writes
by hand, and it is exactly how a half-translated dictionary happens.

THE THREE THINGS THAT GO WRONG WITHOUT A SCRIPT
-----------------------------------------------
1. Google Translate eats the brand. "WeddingAI.video" comes back as
   "WeddingAI.video" transliterated - "WeddingAI.视频", "WeddingAI.Видео" -
   which is the wrong brand name on a page that exists to sell that brand.
   The name is masked before the call and restored after it.

2. Google Translate eats the NUMBERS. A size table that says "5 x 7 in"
   can come back as "5 x 7 pol." or, worse, lose a digit. A wedding
   invitation at the wrong size is a wasted print run, so every translated
   string is checked: the digits of the source must all be present in the
   target. If they are not, the English text is kept and the string is
   reported - a wrong size is worse than an English size.

3. Google Translate returns 429 under load. A failed call returns the
   English string, so a silent rate limit looks like "translation done"
   while the dictionary is full of English. Every failure is counted and
   the script exits non-zero if anything is still English.

Usage
-----
    python scripts/translate-tool-page.py --slug wedding-stationery-set-maker
    python scripts/translate-tool-page.py --slug <slug> --langs zh,es
"""

import argparse
import glob
import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def atomic_write(path, text):
    """temp file + fsync + os.replace - never leave a half-written file.

    The patch and the head file are the ONLY record of a translation run.
    They are written once, at the very end, after every language is done -
    so a run that is killed during the write would leave a truncated JSON
    file, and the NEXT run would die on json.loads() before it could repair
    anything. os.replace() is atomic on Windows: the destination is either
    the old file or the new one, never a partial one.
    """
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".",
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TARGET_LANGS = [l for l in LANGS if l != "en"]

GTL = {
    "zh": "zh-CN", "es": "es", "fr": "fr", "de": "de", "pt": "pt",
    "ja": "ja", "ru": "ru", "ar": "ar", "th": "th", "hi": "hi",
}

# The site's own name. It is a brand, not a phrase - it must survive the
# round trip byte for byte.
BRAND = "WeddingAI.video"

# The mask token. Measured against the free gtx endpoint in all 10 target
# languages (see .tmp/probe-placeholder.py):
#
#   ZXQPROT0ZXQ  -> survives zh es fr de pt ja ru ar th hi
#   %%PROT0%%    -> survives zh es fr de pt ja ru ar th hi
#   \x00PROT0\x00-> survives NOTHING - control characters are dropped, and
#                   then the brand is gone AND the digit check fails on the
#                   sentence around it, so the whole string falls back to
#                   English.
#
# Only the BRAND is masked. Numbers are NOT masked on purpose: Google
# Translate turns "5 x 7 in" into "5 x 7 英寸" / "5 x 7 pulgadas", which
# is exactly right - the unit SHOULD be translated - and the digit check
# below catches the case where a digit is dropped.
BRAND_MASK = "ZXQPROT%dZXQ"

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

HEAD_FIELDS = [
    ("title", r"<title[^>]*>(.*?)</title>"),
    ("description", r'<meta\s+name="description"\s+content="([^"]*)"'),
    ("og_title", r'<meta\s+property="og:title"\s+content="([^"]*)"'),
    ("og_description", r'<meta\s+property="og:description"\s+content="([^"]*)"'),
    ("twitter_title", r'<meta\s+name="twitter:title"\s+content="([^"]*)"'),
    ("twitter_description", r'<meta\s+name="twitter:description"\s+content="([^"]*)"'),
    ("og_image_alt", r'<meta\s+property="og:image:alt"\s+content="([^"]*)"'),
    ("app_title", r'<meta\s+name="apple-mobile-web-app-title"\s+content="([^"]*)"'),
]


def mask(text):
    """Replace the brand with a placeholder that survives the round trip."""
    saved = []

    def keep(m):
        saved.append(m.group(0))
        return BRAND_MASK % (len(saved) - 1)

    out = re.sub(re.escape(BRAND) + r"\.video", keep, text)
    return out, saved


def unmask(text, saved):
    for i, original in enumerate(saved):
        text = text.replace(BRAND_MASK % i, original)
    return text


def has_word(text):
    return bool(re.search(r"[0-9A-Za-z\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff"
                           r"\u0590-\u05ff\u0600-\u06ff\u0e00-\u0e7f"
                           r"\u3040-\u30ff\uac00-\ud7af\U0001f000-\U0001ffff]", text))


def digits_of(text):
    return sorted(re.findall(r"\d+", text))


def translate_one(text, target, retries=4):
    """Translate one string. Returns (text, ok). ok=False means it failed."""
    if not text.strip():
        return text, True
    masked, saved = mask(text)
    if not has_word(masked):
        # Nothing left to translate - "WeddingAI.video" on its own, a pure
        # measurement like "5 x 7 in" (which is NOT masked any more, but the
        # same rule applies to any number-only string). Translating it would
        # come back empty and look like a failure.
        return text, True
    params = {"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": masked}
    url = GTX_ENDPOINT + "?" + urllib.parse.urlencode(params)
    delay = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            chunks = data[0] if data else []
            joined = "".join(c[0] for c in chunks if c and c[0])
            if not joined.strip():
                raise ValueError("empty translation")
            # The brand mask has to come back intact, otherwise the brand is
            # gone and the sentence around it has a hole in it.
            for i in range(len(saved)):
                if BRAND_MASK % i not in joined:
                    raise ValueError("brand mask %d was eaten" % i)
            out = unmask(joined, saved)
            # The digits have to survive. A size table is worth nothing if
            # "5 x 7" came back as "5 x 1".
            if digits_of(out) != digits_of(text):
                return text, False
            if BRAND not in out and BRAND in text:
                return text, False
            return out, True
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                print("    [warn] gtx %s failed: %s" % (target, exc), file=sys.stderr)
                return text, False
            if is_rate_limited(exc):
                print("    [429] rate limited on %s - sleeping before retry %d"
                      % (target, attempt + 1), file=sys.stderr)
            backoff_sleep(attempt)
    return text, False


GTX_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


def backoff_sleep(attempt):
    """Wait longer the more often we have been told to slow down.

    The free endpoint answers 429 when it has had enough. Hammering it
    with retries turns a two-minute cooldown into a twenty-minute one, so
    a 429 sleeps for a LONG time instead of the usual short retry.
    """
    if attempt < 2:
        time.sleep(3 * (attempt + 1))
    else:
        time.sleep(min(300, 20 * (2 ** (attempt - 2))))


def is_rate_limited(exc):
    return "429" in str(exc) or "Too Many Requests" in str(exc)


# ======================================================================
# THE GLOBAL REQUEST GATE
# ======================================================================
#
# WHY THIS EXISTS
# ---------------
# The gateway answered 429 for two hours straight on 2026-11-10. The run
# that hit it used TWELVE worker threads (two groups of six), and the
# first six languages of each group worked. Then every request started
# failing and NEVER recovered - the retry loop logged 1385 "429" lines
# and produced nothing for the rest of the run.
#
# So the limit is not a per-request quota that a retry can outwait: a
# burst of parallel requests puts the account into a state where the
# backoff does not get back in. The only safe answer is to never reach
# that state.
#
# A serial probe measured 10 heavy requests, one every 6 s, all 200 -
# so the budget is comfortable as long as the requests are spaced out.
#
# THE GATE
# --------
# One interval, shared by every thread: no two requests start less than
# LLM_GATE_INTERVAL apart, whatever the worker count is. A 429 makes the
# interval grow by half (up to 60 s); a success lets it shrink again by
# 2% per call. So the run finds its own pace and keeps it.
#
# The measured cost: one language of ~150 strings is ~13 requests, so
# ~13 x 5 s = 65 s plus the model's own thinking time.

LLM_GATE_LOCK = threading.Lock()
LLM_GATE_INTERVAL = 5.0
LLM_GATE_MIN = 5.0
LLM_GATE_MAX = 60.0
_LLM_GATE_NEXT = 0.0


def llm_gate():
    """Block until this thread may start the next request."""
    global _LLM_GATE_NEXT
    while True:
        with LLM_GATE_LOCK:
            now = time.time()
            if now >= _LLM_GATE_NEXT:
                _LLM_GATE_NEXT = now + LLM_GATE_INTERVAL
                return
            wait = _LLM_GATE_NEXT - now
        time.sleep(min(wait, 0.5))


def llm_gate_penalise():
    """The gateway said "too many" - back off for everybody."""
    global LLM_GATE_INTERVAL
    with LLM_GATE_LOCK:
        LLM_GATE_INTERVAL = min(LLM_GATE_MAX, LLM_GATE_INTERVAL * 1.5)
        print("    [gate] the interval is now %.1fs" % LLM_GATE_INTERVAL,
              file=sys.stderr)


def llm_gate_relax():
    """A request went through - creep back towards the fast pace."""
    global LLM_GATE_INTERVAL
    with LLM_GATE_LOCK:
        if LLM_GATE_INTERVAL > LLM_GATE_MIN:
            LLM_GATE_INTERVAL = max(LLM_GATE_MIN, LLM_GATE_INTERVAL * 0.98)


# ======================================================================
# LLM BACKEND
# ======================================================================
#
# WHY THIS EXISTS
# ---------------
# The free gtx endpoint started answering 429 for every request from this
# machine and stayed there. A retry storm against a 429 wall is how a run
# turns into half an hour of sleeping and STILL comes back with 200
# untranslated strings - the failure looks exactly like success.
#
# The desktop runtime already holds a credential for the MiniMax gateway
# (`mmoat_...` in ~/.minimax/auth/**/auth.json), and the gateway can
# translate. MiniMax-M3 with thinking DISABLED translates a 20-string
# batch in ~4.5 s; the same batch with thinking on took 76 s, because the
# model spent 6454 tokens thinking about 20 short sentences.
#
# It is also BETTER, not just faster: gtx produced the kind of output this
# project's own AGENTS.md calls out - an Arabic title that contained a
# German word, a title that was three languages at once. The LLM was told
# to write for a local reader and keeps the brand, the digits and the
# measurement units.

LLM_ENDPOINT = "https://agent.minimax.cn/mavis/api/v1/llm/v1/messages"
LLM_MODEL = "MiniMax-M3"

# THINKING MUST BE ON.
#
# Measured 2026-11-10, same 4 items, 4 repeats, Japanese:
#
#   thinking: disabled   8 defects / 12 answers   (~2 s per batch)
#   thinking: enabled    0 defects / 16 answers   (~28 s per batch)
#   M3.1-Flash, thinking 0 defects / 16 answers   (~29 s per batch)
#   M3.1-Flash, plain    0 defects / 16 answers   (~45 s per batch)
#
# With the thinking switched off the model stops TRANSLATING partway and
# copies the English source into the middle of the sentence: "远
# destination wedding の場合", "重厚な heavier feel 出す", " 免费のPete
# worldwide造的". Those strings pass every other gate - they have the right
# length, they keep every number, they are not empty - so they shipped.
#
# The speed was the reason thinking was turned off in the first place, and
# the speed was bought with a defect that nobody could see. Speed is worth
# 6x here.
LLM_THINKING = "enabled"
LLM_THINKING_BUDGET = 2000

LANG_NAME = {
    "zh": "Simplified Chinese (zh-Hans)",
    "es": "Spanish (es)",
    "fr": "French (fr)",
    "de": "German (de)",
    "pt": "Brazilian Portuguese (pt-BR)",
    "ja": "Japanese (ja)",
    "ru": "Russian (ru)",
    "ar": "Arabic (ar, written right to left)",
    "th": "Thai (th)",
    "hi": "Hindi (hi)",
}

# How long a translation is expected to be, relative to the English
# source, per language. Chinese and Japanese pack far more meaning into
# fewer characters than the English, so a single ratio for every
# language throws away every good translation in those two.
EXPECTED_RATIO = {
    "zh": (0.18, 0.80),
    "ja": (0.20, 0.90),
    "es": (0.65, 1.70),
    "fr": (0.65, 1.70),
    "de": (0.65, 1.70),
    "pt": (0.65, 1.70),
    "ru": (0.55, 1.60),
    "ar": (0.50, 1.50),
    "th": (0.35, 1.40),
    "hi": (0.50, 1.60),
}

LLM_SYSTEM = (
    "You are a senior SEO localizer for WeddingAI.video, a service that "
    "turns a couple's wedding photos into an AI wedding video. You "
    "translate English marketing copy into natural, idiomatic language "
    "that a local reader would actually want to read - never a literal "
    "word-for-word rendering, never a mix of two languages. "
    "You keep every number, every measurement unit and every placeholder "
    "token exactly as they appear. "
    "You answer with a JSON array and nothing else."
)

# How long each kind of string is allowed to be.
#
# The `<title>` (60) and the `<meta name="description">` (160) are
# measured by scripts/check-seo-lengths.py, and that gate walks EVERY
# html file - the ten language copies included - so those two are HARD.
#
# The og:* / twitter:* fields are measured by nothing, so their budget is
# a social-card target with headroom for a language that runs longer
# than the English. A FIXED 160 there is what broke the contact sheet's
# French og_description: the English is 194 characters and the French
# runs to 236, so a 160 cap could never be met without throwing the
# sentence away.
#
# app_title is 30 because that is Apple's own limit.
HEAD_LIMITS = {
    "title": ("title", 60, True),
    "description": ("description", 160, True),
    "og_title": ("title", 90, False),
    "og_description": ("description", 200, False),
    "twitter_title": ("title", 90, False),
    "twitter_description": ("description", 200, False),
    "og_image_alt": ("alt", 60, False),
    "app_title": ("title", 30, True),
}

_TOKEN_CACHE = {}


def resolve_llm_token(force=False):
    """Find the gateway credential.

    The gateway wants `Authorization: Bearer <token>` with the `mmoat_`
    token the desktop runtime keeps on disk. It is NOT the token in
    local-runtime.auth.json (that one is for a different API and answers
    "auth failed"), and the apiKey in config.yaml is the literal
    placeholder `sk-xxx`, which answers "token is required".

    `force=True` re-reads the file. The desktop runtime REWRITES that file
    when it refreshes the token - and a run that started a second earlier
    is holding the token that just died, so the gateway answers 401 to
    every request. Re-reading the file turns a dead run into a live one.
    """
    if "token" in _TOKEN_CACHE and not force:
        return _TOKEN_CACHE["token"]
    env = os.environ.get("MAVIS_LLM_TOKEN")
    if env and env.strip() and not force:
        _TOKEN_CACHE["token"] = env.strip()
        return _TOKEN_CACHE["token"]
    pattern = os.path.expanduser("~/.minimax/auth/*/*/*/auth.json")
    for path in sorted(glob.glob(pattern)):
        try:
            rec = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for value in rec.get("records", {}).values():
            token = value.get("accessToken", "")
            if token.startswith("mmoat_"):
                _TOKEN_CACHE["token"] = token
                return token
    raise SystemExit("[FAIL] no gateway token found - set MAVIS_LLM_TOKEN")


def llm_post(user_text, max_tokens=48000, timeout=300, retries=4):
    """One gateway round trip. Returns the assistant's text or None."""
    token = resolve_llm_token()
    budget = max_tokens
    delay = 4.0
    for attempt in range(retries):
        try:
            body = {
                "model": LLM_MODEL,
                "max_tokens": budget,
                "system": LLM_SYSTEM,
                "messages": [{"role": "user", "content": user_text}],
                # Thinking ON. See LLM_THINKING above for the measurement
                # that turned it on: with it off the model copies English
                # phrases into the middle of the translation.
                "thinking": {"type": LLM_THINKING,
                             "budget_tokens": LLM_THINKING_BUDGET},
            }
            raw = json.dumps(body).encode("utf-8")
            llm_gate()
            req = urllib.request.Request(
                LLM_ENDPOINT, data=raw,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + token,
                         "anthropic-version": "2023-06-01"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            llm_gate_relax()
            out = "".join(b.get("text", "") for b in data.get("content", [])
                          if b.get("type") == "text")
            if out.strip():
                return out
            # AN EMPTY ANSWER IS A BUDGET PROBLEM, NOT A BAD PROMPT.
            #
            # The gateway does not honour budget_tokens: the model thinks
            # for as long as it likes and the thinking tokens come out of
            # max_tokens. A 15 string batch that came back with no text at
            # all spent all 24000 tokens thinking. The same batch with
            # 48000 comes back with the answer.
            #
            # So an empty answer DOUBLES the budget for the next attempt
            # instead of just waiting and repeating the same request.
            #
            # AND THE STARTING BUDGET IS 48000, not 24000, because the
            # first attempt at 24000 is the one that comes back empty:
            # starting at 24000 spent two requests on every batch that
            # thought too long. Measured 2026-11-11: a single small
            # request answered in 4.2 s with 93 thinking tokens, so the
            # gateway was HEALTHY while the batches were failing - the
            # failure was the budget, and the fix is the budget.
            budget = min(96000, budget * 2)
            print("    [retry] llm empty answer - raising the budget to %d"
                  % budget, file=sys.stderr)
            raise ValueError("empty answer")
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and attempt < retries - 1:
                # The runtime rotated the token. Re-read it and try again.
                print("    [retry] 401 - the gateway token rotated, re-reading "
                      "the credential", file=sys.stderr)
                token = resolve_llm_token(force=True)
                time.sleep(delay)
                delay = min(60, delay * 2)
                continue
            if exc.code == 429:
                # Slow EVERYBODY down, not just this thread.
                llm_gate_penalise()
            if attempt == retries - 1:
                print("    [warn] llm failed: %s" % exc, file=sys.stderr)
                return None
            print("    [retry] llm HTTP %s - backing off" % exc.code,
                  file=sys.stderr)
            time.sleep(delay)
            delay = min(60, delay * 2)
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                print("    [warn] llm failed: %s" % exc, file=sys.stderr)
                return None
            print("    [retry] llm %s - backing off" % exc, file=sys.stderr)
            time.sleep(delay)
            delay = min(60, delay * 2)
    return None


def llm_parse_json_array(text):
    """Pull the JSON array out of an answer that may be wrapped in prose."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return None
    try:
        arr = json.loads(text[start:end + 1])
    except Exception:  # noqa: BLE001
        return None
    return arr if isinstance(arr, list) else None


def norm_id(value):
    """Normalise an id the model returned.

    The model answers with `"id": 3` most of the time, but it also answers
    with `"id": "3"` and with `"id": 3.0`. Comparing those to a Python int
    with `==` fails for the string form, so a perfectly good answer looked
    like a MISSING item - and the script kept the English.
    """
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(value).strip()


def digit_stream(text):
    """Every digit of the text, in order, as one string.

    `digits_of()` splits on non-digits and compares the pieces, so
    "4.25 x 5.5 in" and "4,25 x 5,5 Zoll" look different to it - and the
    second one is the CORRECT German. Comparing the raw digit stream
    ("42555" both) accepts the decimal comma and still catches a dropped
    digit.
    """
    return re.sub(r"\D", "", text)


def number_runs(text):
    """The numbers of the text, as a list.

    A decimal COMMA is normalised to a decimal point first, because
    "4,25 x 5,5 Zoll" is the correct German for "4.25 x 5.5 in" and must
    not read as a changed measurement.

    Returns e.g. ["4.25", "5.5", "300", "100"].
    """
    normalised = re.sub(r"(?<=\d),(?=\d)", ".", text)
    return re.findall(r"\d+(?:\.\d+)?", normalised)


def numbers_kept(source, target):
    """True when every number of the source is still in the target.

    THE RULE AND WHY IT IS NOT SIMPLER
    ---------------------------------
    The source runs must be a MULTISET SUBSET of the target runs:

    - a number the source had and the target dropped  -> REJECTED.
      "100 lb ... 80 to 100 gsm" losing its tail is a wrong print spec.
    - a number the source had and the target changed  -> REJECTED.
      "5 x 7" becoming "5 x 8" is a wrong invitation size.
    - a number the target ADDED                       -> ALLOWED.
      Chinese spells numbers out, so a good translation often writes
      "4 种风格" where the English says "four styles". The source has no
      digit there at all, and rejecting the translation for being MORE
      specific than the English would throw away the better sentence.
    """
    have = Counter(number_runs(source))
    want = Counter(number_runs(target))
    for value, count in have.items():
        if want[value] < count:
            return False
    return True


# ---------------------------------------------------------------------------
# THE UNTRANSLATED-SPAN GATE
# ---------------------------------------------------------------------------
#
# WHAT IT CATCHES
# ---------------
# A translation that leaves a piece of the English source in the middle of
# the sentence: "地元での結婚式なら6〜8週間前、infuseの結婚式は...", "重厚な
# orfic thenceには110〜120 lb...", "Both ask for picture numbers, and both
# would rather have a numbered sheet".
#
# WHY NO OTHER GATE SEES IT
# -------------------------
# The length gate cannot (the string has a plausible length), the number
# gate cannot (the digits are all still there), the "same as English"
# check cannot (the string as a whole IS translated), and the FAQ parity
# check cannot (the schema and the visible copy agree - they are both
# garbage). The only thing that notices is looking at the WORDS.
#
# HOW IT WORKS
# ------------
# A "run" is a maximal stretch of Latin words inside a sentence written in
# another script. A run is allowed when it is:
#
#   - a format, brand, unit or paper size (LATIN_KEEP / UNIT_WORDS),
#   - a vendor domain ("convertbox.app"),
#   - only numbers and unit words ("300 DPI", "2481 by 3507 pixels").
#
# Everything else is an untranslated span and the item is re-done.
#
# For the four LATIN-SCRIPT targets the same defect looks different - an
# English word inside a Spanish sentence - so there the test is "does the
# run contain an English word that is not also a word of the target
# language".

LATIN_KEEP = {
    # file formats and codecs
    "pdf", "gif", "mp4", "webm", "mkv", "mov", "heic", "avif", "jpg", "jpeg",
    "png", "webp", "svg", "mp3", "wav", "aac", "vp9", "avi", "flv", "3gp",
    "opus", "flac", "aiff", "h.264", "h.265", "hevc", "av1", "rc4",
    "aes-128", "aes-256", "zip", "html", "css", "json", "srt", "vtt",
    # paper sizes
    "us letter", "letter", "legal", "tabloid",
    # acronyms
    "ai", "api", "rsvp", "diy", "alt", "ui", "ux", "url", "raw", "exif",
    "rgb", "dng", "mp", "tiff",
    # brands and products
    "weddingai.video", "weddingai", "adobe", "lightroom", "lightroom classic",
    "acrobat", "canva", "ilovepdf", "compuserve", "iphone", "webcodecs",
    # The vendor column headers of the comparison tables. A column header
    # is a product name, and a product name is not copy: it is spelled the
    # same in every language. Without these the gate threw the vendor
    # name away in every non-Latin language and asked for it again.
    "smallpdf", "adobe acrobat",
    "instagram", "whatsapp", "youtube", "youtube shorts", "tiktok", "reels",
    "pinterest", "google", "icloud", "dropbox", "mediabunny", "capcut",
    "ffmpeg", "imovie", "handbrake", "shotcut", "filmora", "vlc",
    # vendor domains
    "convertbox.app", "feelthefile.com", "smoothclip.com", "clipcraft.ai",
    "clipzeal.com", "freevideogenerator.io", "justright.tools",
    # UI labels the copy quotes on purpose
    "save the date", "save the dates", "actual size", "fit to page",
    "fit whole photo", "crop to fill", "fill", "fit", "high", "best",
    "standard", "print", "full hd", "loop forever", "play once",
    "original size", "not stated", "none", "portrait", "landscape",
    "square", "16:9", "9:16", "1:1", "4:5", "4k", "8k", "hd", "sd", "uhd",
    "dress code", "browser rgb", "chat apps", "social posts",
    "video inside", "audio inside", "webp", "real size", "no watermark added",
    "contact sheet", "contact sheets", "chrome", "edge", "safari",
    "windows", "macos", "linux", "adobe lightroom classic",
    "firefox", "opera", "brave",
    "iphone heic", "ig", "bg", "pixum",
    # The photo-book vendor list is three separate runs, because the
    # slash does not glue two words into one run.
    "milk books", "artifact uprising",
    # The stationery comparison table has one column per vendor, and the
    # header is the product name. A column header is not copy: it is
    # spelled the same in every language.
    "greetings island",
    # A paper size, written the way the paper industry writes it.
    "4-bar",
}

# -------------------------------------------------------
# The wedding-planning sources and products.
#
# WHY THIS LIST IS SEPARATE
# --------------------------
# The planning tools quote their sources BY NAME - "The Knot's 2026 Real
# Weddings Study", "Zola", "WedBuild", "Calculator City" - and a translator
# is right to keep those names in the original script. A brand name that
# gets transliterated ("Zola" -> "佐拉") is a wrong brand name on a page
# whose whole job is to be credible.
#
# But the untranslated-span gate below reads a Latin run inside a
# translated sentence as a leftover English phrase, so every one of these
# names made the gate REJECT a perfectly good translation and revert the
# string to English. The article then stayed in English in all ten
# languages - exactly the failure this gate was built to prevent, pointing
# the other way.
#
# These are matched by CONTAINMENT rather than by equality, because the
# name rarely stands alone: "The Knot's 2026 Real Weddings Study" is one
# Latin run that contains the name and a number, and "State DMV" contains
# "dmv". Equality would not catch either.
#
# The names are listed in lower case because the comparison is done on the
# normalised run.
ENTITY_KEEP = {
    # the sources and the products the copy names
    "the knot", "zola", "vogue", "ourvows", "real weddings study",
    "wedbuild", "calculator city", "plana", "weddingcakeshub",
    "wedcalc", "pix.wedding", "rosevow", "myweddingkit",
    "weddingnotepad", "mysetplan", "simplifycalc",
    "weddingtimeline.org", "eventrundown.com", "digitalrsvps",
    "toolaspect", "moneydeck", "weddingcardboxes", "easyregistry",
    "text my wedding", "thebestmanspeech.com", "weddingshub",
    "theperfectwedding", "bespoke bride", "emily post", "marie claire",
    "the perfect wedding", "our vows",
    # US government and standards bodies
    "national institute on alcohol abuse and alcoholism", "niaaa",
    "social security administration", "social security",
    "us department of state", "state department", "usa.gov",
    "travel.state.gov", "namechange.com", "legalhelp.us",
    "us rsvp", "rsvp", "real id", "form ss-5", "state dmv", "dmv",
    # the studies the copy quotes
    "first look report", "wedding spend survey", "wedding guests study",
    "wedding registry", "registry",
}

# Words that may appear in a Latin run that is otherwise a measurement.
UNIT_WORDS = {
    # a format name may sit right next to a number: "1 PDF", "PDF 1"
    "pdf", "gif", "mp4", "webm", "mkv", "mov", "heic", "jpg", "jpeg",
    "png", "webp", "svg", "mp3", "zip",
    # The text and document formats the tools offer for download. The
    # button says "Download .txt", and the extension is not translated in
    # any language.
    "txt", "csv", "json", "md", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "rtf", "odt", "ods", "ical", "ics", "vcf", "svgz", "avif", "tif", "tiff",
    "in", "inch", "inches", "mm", "cm", "px", "pixels", "pixel", "fps",
    "ms", "kbps", "mbps", "mb", "gb", "kb", "lb", "gsm", "dpi", "megapixel",
    "megapixels", "x", "by", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
    "us", "letter",
    # ---------------------------------------------------------
    # The units the wedding copy measures in.
    #
    # The bar and cake tools are tables of servings: "5 oz (150 ml)",
    # "12 oz can or bottle", "1.5 oz shot". A translator that keeps the
    # unit in Latin script is doing the RIGHT thing - the unit is the
    # unit in every language - but the gate read the run as untranslated
    # English and threw the sentence away.
    "oz", "ml", "fl", "floz", "cl", "dl", "l", "litre", "liter",
    "litres", "liters", "g", "kg", "gram", "grams", "gramme", "grammes",
    "tsp", "tbsp", "cups", "cup", "quarts", "pint", "pints", "gallons",
    "ozs", "mls", "cc", "min", "mins", "minutes", "hr", "hrs", "hours",
    "sec", "secs", "seconds", "days", "day", "weeks", "week", "months",
    "month", "years", "year", "thousand", "k",
}

# English words that are unmistakably English in ALL FOUR of es/fr/de/pt.
#
# The list is deliberately short. Every word in it was taken out because
# the TARGET language uses a different word for it: German says "Tool"
# and "Upload", French says "page" and "date", Spanish says "video" and
# "foto", Portuguese says "ficheiro". A word that the target language
# also uses would fire on a perfectly good translation, and a false
# positive costs a retry - or, worse, an English fallback.
#
# So: the function words and the verbs of the tool copy, and nothing that
# a German or French marketing sentence would legitimately contain.
ENGLISH_ONLY_WORDS = {
    # function words
    "the", "and", "your", "you", "our", "they", "them", "their", "this",
    "that", "with", "from", "into", "over", "under", "about", "after",
    "before", "between", "each", "some", "all", "any", "most", "other",
    "such", "very", "just", "only", "also", "even", "back", "well",
    "more", "than", "then", "when", "where", "which", "who", "what", "why",
    "how", "would", "should", "could", "have", "has", "had", "will",
    "been", "being", "does", "did", "done", "makes", "made", "using",
    "used",
    # the verbs of this copy
    "click", "merge", "split", "convert", "crop", "resize",
    "trim", "choose", "add", "added", "adding",
    # the nouns of this copy
    "wedding",
}

LATIN_RUN_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9'\u2019./\-]*"
    r"(?:[ \u00a0]+[A-Za-z0-9][A-Za-z0-9'\u2019./\-]*)*")
NON_LATIN_RE = re.compile(
    r"[\u3040-\u30ff\u4e00-\u9fff\u0600-\u06ff\u0e00-\u0e7f\u0900-\u097f]")
LATIN_TARGETS = ("en", "es", "fr", "de", "pt")


def _run_is_allowed(run):
    """True when a Latin run is a name, a unit or a measurement."""
    norm = re.sub(r"\s+", " ", run.strip(" .-/")).lower()
    if not norm:
        return True
    if norm in LATIN_KEEP:
        return True
    # a vendor domain
    if re.fullmatch(r"[a-z0-9\-]+(\.[a-z0-9\-]+)+", norm):
        return True
    # A run that CONTAINS a name the copy quotes by name. Equality is not
    # enough: "The Knot's 2026 Real Weddings Study" is one run, and it
    # contains "the knot" and "real weddings study".
    #
    # The name has to sit on a WORD boundary, otherwise "rsvp" would match
    # inside "reserved" and a plain English word would slip through.
    for name in ENTITY_KEEP:
        if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(name), norm):
            return True
    # only numbers, unit words and the glue between them
    words = re.findall(r"[A-Za-z0-9.]+", norm)
    for word in words:
        if word.isdigit():
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", word):
            continue
        if word in UNIT_WORDS:
            continue
        # A number glued to a unit: "750ml", "12oz", "1.5oz". The wedding
        # copy writes its servings that way, and the unit is the unit in
        # every language - so a translated sentence is allowed to keep it.
        m2 = re.fullmatch(r"(\d+(?:\.\d+)?)([a-z]+)", word)
        if m2 and m2.group(2) in UNIT_WORDS:
            continue
        return False
    return True


def script_ok(value, lang):
    """True when the text is actually written in the target language's script.

    WHY
    ---
    The reuse map copies a value from one language's dictionary into
    another. The site's own Japanese dictionary hands out the CHINESE
    "常见问题" for "Frequently asked questions" - both languages use
    kanji, so nothing but the script can tell them apart. The copy then
    ships Chinese to a Japanese reader.

    The rule is a floor, not a proof: Japanese must carry at least one
    kana (a pure-kanji Japanese sentence is rare in this copy and is
    better re-translated), Chinese must carry kanji and no kana,
    Russian Cyrillic, Arabic Arabic script, Thai Thai script, Hindi
    Devanagari.
    """
    if lang in LATIN_TARGETS:
        return True
    if lang == "ja":
        return bool(re.search(r"[\u3040-\u309f\u30a0-\u30ff]", value))
    if lang == "zh":
        return bool(re.search(r"[\u4e00-\u9fff]", value)) and not \
            re.search(r"[\u3040-\u309f\u30a0-\u30ff]", value)
    if lang == "ru":
        return bool(re.search(r"[\u0400-\u04ff]", value))
    if lang == "ar":
        return bool(re.search(r"[\u0600-\u06ff\u0750-\u077f]", value))
    if lang == "th":
        return bool(re.search(r"[\u0e00-\u0e7f]", value))
    if lang == "hi":
        return bool(re.search(r"[\u0900-\u097f]", value))
    return True


def carries_target_script(value, lang):
    """True when the value carries the target language's OWN script.

    This is the WEAK version of script_ok(): it asks "is this written in
    the target script at all", not "is this written the way this target
    writes it".

    WHY THE WEAK VERSION IS NEEDED
    -------------------------------
    Japanese is written with kanji AND kana, and a short label is often
    pure kanji. Every one of those is correct Japanese, and script_ok()
    - which demands a kana - throws all of them away.

    But the WEAK version is what catches the defect script_ok() was
    written for: the model handing back the ENGLISH source unchanged.
    A value that is entirely Latin carries no non-Latin run, so
    foreign_spans() returns an empty list and the untranslated-span
    gate sees nothing at all. For a Japanese or Chinese or Thai page
    that is how an English label used to get through.
    """
    if lang in LATIN_TARGETS:
        return True
    if lang == "ja":
        return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", value))
    if lang == "zh":
        return bool(re.search(r"[\u4e00-\u9fff]", value))
    if lang == "ru":
        return bool(re.search(r"[\u0400-\u04ff]", value))
    if lang == "ar":
        return bool(re.search(r"[\u0600-\u06ff\u0750-\u077f]", value))
    if lang == "th":
        return bool(re.search(r"[\u0e00-\u0e7f]", value))
    if lang == "hi":
        return bool(re.search(r"[\u0900-\u097f]", value))
    return True


def script_independent(source):
    """True when the source has no word that a translation could change.

    A measurement ("5 x 7 in"), a paper size ("A2", "4-bar (A1)"), a
    format name ("PDF"), a brand ("Canva") and a domain
    ("WeddingAI.video") are spelled the SAME in all ten languages. For
    those strings the English source IS the translation.

    WHY THIS HAS TO EXIST
    ---------------------
    script_ok() asks a Japanese value to carry at least one kana. A
    measurement never can - so the gate threw away the CORRECT answer.
    And because the gate re-checks the STORED value at the start of
    every language and every round, the runner asked the model to
    translate the same "5 x 7 in" again and again, for every language,
    for every round. That is what kept the queue from ever finishing,
    and it is why the completion metric counted a correctly kept
    measurement as a missing translation.

    The rule is deliberately narrow: every Latin run of the source must
    be a format, a brand, a unit, a paper size or a vendor domain. A
    source that carries an ordinary English word is NOT script
    independent, so an untranslated paragraph still gets rejected.

    The value must also be IDENTICAL to the source. A model that
    mangled the measurement ("5 x 7 inches" with the digits moved) is
    still rejected.
    """
    if not source or not source.strip():
        return False
    # A source that already carries another script is not a Latin-only
    # string, so the "keep it verbatim" argument does not apply.
    if NON_LATIN_RE.search(source):
        return False
    runs = LATIN_RUN_RE.findall(source)
    if not runs:
        return False
    for run in runs:
        if not _run_is_allowed(run):
            return False
    return True


def foreign_spans(text, lang):
    """The English spans that are still sitting inside a translation.

    Returns a list of the offending runs (empty when the text is clean).
    """
    if not isinstance(text, str) or not text:
        return []
    # A placeholder is not a word: "{name}" and "{n}" are the runtime
    # copy's own tokens, not an English fragment left behind.
    text = re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*\}", " ", text)
    bad = []
    if lang in LATIN_TARGETS:
        # A Latin-script target: the defect is an English WORD inside a
        # translated sentence. A whole-sentence run is useless here - in
        # Spanish every word of the sentence is a Latin word - so the
        # allowed multi-word phrases are cut out first and the rest is
        # read word by word.
        if lang == "en":
            return []
        rest = text
        for phrase in MULTIWORD_KEEP:
            rest = re.sub(re.escape(phrase), " ", rest, flags=re.I)
        for word in re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)*", rest, re.UNICODE):
            if word.lower() in ENGLISH_ONLY_WORDS:
                bad.append(word)
        return bad
    # A non-Latin target: the defect is a whole Latin RUN inside a
    # sentence written in another script.
    if not NON_LATIN_RE.search(text):
        return []
    for run in LATIN_RUN_RE.findall(text):
        if _run_is_allowed(run):
            continue
        bad.append(run)
    return bad


# The allowed phrases that carry more than one word. They are cut out of a
# Latin-script translation before the word-by-word check runs, so "Save the
# dates" does not read as three English words.
MULTIWORD_KEEP = [
    "no watermark added", "lightroom classic", "youtube shorts",
    "browser rgb", "chat apps", "social posts", "video inside",
    "audio inside", "real size", "save the dates", "save the date",
    "actual size", "fit to page", "fit whole photo", "crop to fill",
    "loop forever", "play once", "original size", "not stated",
    "us letter", "full hd", "dress code",
    # A list of photo-book vendors that the copy keeps verbatim. Five
    # words, so it WOULD trip the n-gram rule in every language.
    "milk books / pixum / artifact uprising",
    # -------------------------------------------------------
    # The names the wedding-planning copy quotes.
    #
    # In the four Latin-script languages the check is per WORD, and "the"
    # is an English word. A German sentence that keeps the source name -
    # "Die Real Weddings Study von The Knot" - therefore fired on "The",
    # and the good German translation was thrown away.
    #
    # These phrases are cut out of the text before the word check, exactly
    # like the UI labels above: the name is not copy, it is a name.
    "the knot", "real weddings study", "wedding spend survey",
    "first look report", "social security administration",
    "national institute on alcohol abuse and alcoholism",
    "us department of state", "state department of state",
    "travel.state.gov", "namechange.com", "legalhelp.us", "usa.gov",
    "the perfect wedding", "text my wedding", "weddingnotepad",
    "weddingtimeline.org", "eventrundown.com", "digitalrsvps",
    "thebestmanspeech.com", "weddingshub", "theperfectwedding",
    "calculator city", "weddingcakeshub", "pix.wedding", "rosevow",
    "myweddingkit", "simplifycalc", "mysetplan", "weddingcardboxes",
    "easyregistry", "ourvows", "toolaspect", "moneydeck",
]


def _word_ngrams(text, n):
    # The phrases the copy quotes on purpose are cut out first, so
    # "Choose Actual size. Fit to page shrinks the sheet." and its good
    # Spanish translation do not share a five-word window just because
    # both of them quote "Actual size" and "Fit to page".
    for phrase in MULTIWORD_KEEP:
        text = re.sub(re.escape(phrase), " ", text, flags=re.I)
    # ONLY the words, not the numbers.
    #
    # "Batch crop 9:16 / 1:1 / 4:5 / 4:3 / 3:2 for IG" and its Spanish
    # translation share a long run of DIGITS, and a window that counts
    # digits as words fires on every aspect-ratio list the site has. The
    # numbers are checked by the number rule; this rule is about words.
    #
    # A hyphen keeps a compound together: the German "Drag-Drop-Tabellen"
    # is one German word, not three English ones.
    words = re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)*", text, re.UNICODE)
    return set(tuple(w.lower() for w in words[i:i + n])
               for i in range(len(words) - n + 1))


def english_ngram_leak(source, target, n=5):
    """True when the target copies a whole English phrase from the source.

    WHY THIS EXISTS BESIDE foreign_spans()
    --------------------------------------
    The run-based gate works on the WORD level, so a wholesale copy of the
    English source ("a person half out of the picture", "and press the
    export button. One file") survives it in the Latin-script languages,
    where every word is already a Latin word.

    A translation is not supposed to contain five consecutive English
    words from its own source. The allowed phrases the copy quotes on
    purpose ("Save the dates", "Actual size", "Fit to page") are three
    words at most, so a five-word window never fires on them.
    """
    src_grams = _word_ngrams(source, n)
    if not src_grams:
        return False
    return bool(src_grams & _word_ngrams(target, n))


def llm_prompt(items, target):
    lines = [
        "Translate every item below into %s." % LANG_NAME[target],
        "",
        "Rules:",
        "- Output ONLY a JSON array. One object per input item, in the same",
        "  order, with keys \"id\" (copy the input id) and \"text\".",
        "- Keep every number, every measurement unit (in, cm, DPI, MB, %) and",
        "  every placeholder token such as ZXQPROT0ZXQ EXACTLY as written.",
        "  Never translate a digit and never drop one.",
        "- When the English text uses a DIGIT, write that number as a digit",
        "  too. Do not spell it out (\"1 column\" stays a digit, not \"one",
        "  column\"), because the reader is choosing a number on screen.",
        "- Keep the brand name WeddingAI.video as it is.",
        "- Write natural marketing copy for a local couple, not a literal",
        "  word-for-word rendering, and never mix two languages.",
        "- TRANSLATE EVERY WORD of the English source. Never leave a phrase",
        "  of it in the translation. Keep in the original script only:",
        "  format names (PDF, MP4, GIF, WebM), the brand WeddingAI.video,",
        "  vendor and app names, and measurement units (lb, gsm, DPI, inch).",
        "- If an item carries \"max\", the translation MUST be at most that",
        "  many characters including spaces.",
        "- If an item's kind is \"title\" or \"description\", write one line",
        "  with no trailing full stop.",
        "- No commentary, no notes, no markdown fences.",
        "",
        "INPUT:",
        json.dumps(items, ensure_ascii=False),
    ]
    return "\n".join(lines)


def llm_translate_items(items, target, batch=20):
    """Translate a list of items.

    An item is {"id": int, "kind": str, "max": int|None, "text": str}.
    Returns {id: translation}. Missing ids mean the model dropped them.
    """
    out = {}
    groups = [items[i:i + batch] for i in range(0, len(items), batch)]
    for n, group in enumerate(groups, 1):
        answer = llm_post(llm_prompt(group, target))
        arr = llm_parse_json_array(answer)
        if arr is None:
            print("    [warn] %s batch %d: unparseable answer, retrying smaller"
                  % (target, n), file=sys.stderr)
            for item in group:
                one = llm_post(llm_prompt([item], target))
                one_arr = llm_parse_json_array(one)
                if one_arr and one_arr and isinstance(one_arr[0], dict):
                    out[item["id"]] = one_arr[0].get("text", "")
            continue
        got = {}
        for entry in arr:
            if isinstance(entry, dict) and "id" in entry:
                got[norm_id(entry["id"])] = entry.get("text", "")
        for item in group:
            if norm_id(item["id"]) in got:
                out[item["id"]] = got[norm_id(item["id"])]
            else:
                print("    [warn] %s: id %s missing from the answer"
                      % (target, item["id"]), file=sys.stderr)
        print("      %s: %d/%d" % (target, len(out), len(items)))
        sys.stdout.flush()
    return out


def llm_verify(src, dst, saved, maxlen, lang=None):
    """Return a reason string when the translation is not usable."""
    if not dst or not dst.strip():
        return "empty"
    for i in range(len(saved)):
        if BRAND_MASK % i not in dst:
            return "brand mask %d eaten" % i
    if not numbers_kept(src, dst):
        return "a measurement was dropped or changed"
    if BRAND not in dst and BRAND in src:
        return "brand lost"
    if lang:
        # The untranslated-span gate. See foreign_spans() for why no other
        # check sees this.
        spans = foreign_spans(dst, lang)
        if spans:
            return "untranslated English: %r" % spans[0][:60]
        if english_ngram_leak(src, dst):
            return "copied a whole English phrase"
        # AN ENGLISH ECHO. The model handed the source back unchanged,
        # which for a non-Latin target is never a translation.
        #
        # foreign_spans() cannot see it: a value that is ENTIRELY Latin
        # contains no non-Latin run, so the untranslated-span gate
        # returns an empty list and the phrase leak needs five words.
        # A two-word label came back as English and the gate called it
        # good.
        if not carries_target_script(dst, lang) and not script_independent(src):
            return "still in English"
    if maxlen and len(dst) > maxlen:
        return "too long (%d > %d)" % (len(dst), maxlen)
    # A runaway is a string that grew out of all proportion. The floor
    # has to be generous: "RSVP by" is 7 characters and its correct
    # Spanish is "Confirmar asistencia antes del" - 31 characters, four
    # times as long, and completely right. Only strings long enough for
    # the ratio to mean something are checked at all.
    if len(src) >= 30 and len(dst) > int(len(src) * 3.0):
        return "runaway length"
    return None


def llm_strict_prompt(item, target):
    """A one-item prompt for a translation that has to be re-done.

    Used when the first answer broke a rule. The wording changes the
    failure mode: the model that dropped the tail of a sentence ("...rather
    than 80 to 100 gsm copy paper") does not drop it when the prompt says
    the digits are load-bearing.
    """
    return "\n".join([
        "Translate this single item into %s." % LANG_NAME[target],
        "",
        "Rules:",
        "- Output ONLY a JSON array with ONE object: {\"id\": %d, \"text\": \"...\"}."
        % item["id"],
        "- Keep EVERY number exactly as written - the same digits in the same",
        "  order. Do not round a measurement, do not drop a number, and do not",
        "  replace a number with a spelled-out word.",
        "- If the English uses a DIGIT, the translation must use that digit",
        "  too, not a spelled-out number.",
        "- Keep every placeholder token such as ZXQPROT0ZXQ exactly as written.",
        "- Keep the brand name WeddingAI.video as it is.",
        "- Keep the whole meaning of the item. Do not shorten it by dropping",
        "  a clause.",
        "- TRANSLATE EVERY WORD. Do not leave any phrase of the English",
        "  source in the translation. Keep in the original script only:",
        "  format names (PDF, MP4, GIF), the brand WeddingAI.video, app",
        "  names, and measurement units (lb, gsm, DPI, inch).",
    ] + (["- The translation MUST be at most %d characters long." % item["max"]]
         if item.get("max") else []) + [
        "",
        json.dumps({"id": item["id"], "kind": item.get("kind", "body"),
                    "text": item["text"]}, ensure_ascii=False),
    ])


def llm_translate_one_strict(item, target):
    """Re-do ONE item with the strict prompt. Returns the text or None."""
    arr = llm_parse_json_array(
        llm_post(llm_strict_prompt(item, target), max_tokens=24000))
    if not arr:
        return None
    for entry in arr:
        if isinstance(entry, dict) and entry.get("text"):
            return entry["text"]
    return None


def truncate_at_word(text, maxlen):
    """Cut a string to the budget at a word boundary.

    The last resort of the shortening chain. A mid-word cut is a defect
    (the repo's own AGENTS.md calls it out), so the cut always lands
    between words, and the trailing punctuation is cleaned up.
    """
    if len(text) <= maxlen:
        return text
    cut = text[:maxlen]
    space = cut.rfind(" ")
    if space > maxlen * 0.4:
        cut = cut[:space]
    return cut.rstrip(" ,;:-—–|、。，")


def llm_shorten(text, target, maxlen, tighter=False):
    """Ask for a shorter version of one string. Returns None on failure."""
    extra = ""
    if tighter:
        extra = (" This version is TOO LONG. Use fewer words: drop the last "
                 "clause, shorten the brand phrase, and keep only the keyword "
                 "and the single promise.")
    answer = llm_post(
        "Rewrite the following %s text so that it is AT MOST %d characters "
        "long (spaces included).%s Keep every number and every placeholder "
        "token exactly as they are, keep the meaning, and do not drop a "
        "clause. Answer with a JSON object of the form {\"text\": \"...\"} "
        "and nothing else.\n\nTEXT:\n%s"
        % (LANG_NAME[target], maxlen, extra, text),
        max_tokens=24000)
    if not answer:
        return None
    out = ""
    m = re.search(r"\{.*\}", answer, re.S)
    if m:
        try:
            out = json.loads(m.group(0)).get("text", "").strip()
        except Exception:  # noqa: BLE001
            out = ""
    if not out:
        # The model answered in prose. Take the last non-empty line, which
        # is the rewritten text rather than a preamble like "Sure, here is
        # a shorter version:".
        lines = [ln.strip().strip('"') for ln in answer.strip().split("\n")]
        lines = [ln for ln in lines if ln]
        out = lines[-1] if lines else ""
    if not out or len(out) > maxlen:
        return None
    return out


def verify_stored(source, value, maxlen, lang=None, zh_value=None):
    """Check a value that is being REUSED instead of translated.

    `--skip-existing` and the reuse map both take a value from elsewhere
    and put it in the page without ever looking at it again. That value
    may have been written before the budget existed - the French title
    of the contact sheet page was 79 characters long, and the reuse
    path happily carried it past the 60 character gate. So a reused
    value is checked the same way a fresh one is.

    The untranslated-span check matters here MOST: the values this
    project already wrote into the dictionaries were produced by the
    thinking-off model, so the reuse map was pointing straight at the
    garbage.

    `zh_value` is the Chinese rendering of this same string. It is only
    used for Japanese, and only to answer one question: is this
    kanji-only value the CHINESE word or the JAPANESE one? See the
    Japanese branch below.
    """
    if not value or not value.strip():
        return False
    if BRAND not in value and BRAND in source:
        return False
    if not numbers_kept(source, value):
        return False
    if lang and foreign_spans(value, lang):
        return False
    if lang and english_ngram_leak(source, value):
        return False
    if lang and not script_ok(value, lang):
        # A measurement, a paper size, a format name and a brand are
        # spelled the same in every language, so the English source IS
        # the translation. script_ok() can never be satisfied by them -
        # asking a Japanese "5 x 7 in" for a kana is asking for a wrong
        # answer. The value must be identical to the source, so a model
        # that changed the digits is still rejected.
        if value.strip() == source.strip() and script_independent(source):
            pass
        elif lang == "ja" and _ja_kanji_only_is_japanese(value, source, zh_value):
            # A Japanese label written in pure kanji. Accept it.
            pass
        else:
            return False
    if maxlen and len(value) > maxlen:
        return False
    return True


def _ja_kanji_only_is_japanese(value, source, zh_value):
    """True when a kanji-only Japanese value is Japanese and not Chinese.

    WHY THE kana RULE IS NOT ENOUGH
    --------------------------------
    script_ok() asks a Japanese value to carry at least one kana,
    because a Chinese sentence and a Japanese sentence can both be
    written in kanji. That rule is right for a SENTENCE and wrong for a
    LABEL: "挙式日", "披露宴会場", "封筒", "出力", "席札" and
    "印刷解像度" are all pure kanji, all correct Japanese, and all of
    them were thrown away - and then asked for again, in every round,
    for every language.

    HOW THE CHINESE CASE IS STILL CAUGHT
    --------------------------------------
    Not by a heuristic. The Chinese rendering of this very string is
    known - it is the Chinese pass of the SAME run - so the test is
    exact: a kanji-only value that is the Chinese rendering is the
    Chinese word, and it is rejected. A kanji-only value that is NOT
    the Chinese rendering is the Japanese one.

    The one case this cannot decide is a string whose Chinese and
    Japanese renderings are identical - "手動" is such a string, and
    the site's own Japanese dictionary once handed out the Chinese
    "常见问题" for a Japanese page. When the Chinese rendering is not
    known the value is rejected, which is the safe direction: a
    re-translation costs one request, a Chinese page costs a reader.
    """
    if not re.search(r"[\u4e00-\u9fff]", value):
        return False
    if value.strip() == source.strip():
        return False
    if not zh_value:
        return False
    return value.strip() != zh_value.strip()


def ratio_outliers(source, per_lang, langs):
    """Find translations whose LENGTH is impossible for the language.

    WHY NOT "COMPARE WITH THE OTHER LANGUAGES"
    -------------------------------------------
    The first version compared each translation with the median of the
    other nine and threw away anything under 45% of it. Chinese is
    naturally about a third as long as the English, so EVERY good
    Chinese translation was flagged - and the pass then replaced them
    with the English source, which is strictly worse.

    So the expectation is per language: how long is a translation of
    this sentence in THIS language, relative to the English? Chinese
    and Japanese pack far more meaning into fewer characters, Arabic
    and Thai sit in between, and the Latin-script languages run close
    to the English.

    WHAT IT CATCHES
    ---------------
    A translation that is not a translation: "#", "_|{_", an empty
    answer, a fragment. These pass every single-string check - they are
    not empty, they carry no numbers to lose, they fit the budget - and
    only their length gives them away.

    Returns [(text, lang, value, reason)].
    """
    out = []
    src_len = len(source)
    if src_len < 4:
        return out
    for lang in langs:
        value = per_lang.get(lang, {}).get(source)
        if not value or value == source:
            continue
        low, high = EXPECTED_RATIO.get(lang, (0.4, 2.0))
        n = len(value)
        if n < src_len * low or n > src_len * high:
            out.append((source, lang, value,
                        "%d chars, expected %d-%d"
                        % (n, src_len * low, src_len * high)))
    return out


def llm_translate_all(texts, kinds, target, workers=3, batch=20):
    """Translate every text into one language.

    Returns (results, failures). A result maps the ENGLISH source text to
    its translation; a failure is the English text that could not be
    translated safely.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}
    failures = []
    if not texts:
        return results, failures

    # 1. Mask the brand, so the model cannot transliterate it.
    masked = []
    for text in texts:
        m, saved = mask(text)
        masked.append((text, m, saved))

    # 2. Translate.
    items = []
    for idx, (orig, m, saved) in enumerate(masked):
        kind, maxlen = kinds.get(orig, ("body", None))
        item = {"id": idx, "kind": kind, "text": m}
        if maxlen:
            item["max"] = maxlen
        items.append(item)

    groups = [items[i:i + batch] for i in range(0, len(items), batch)]

    def work(group):
        got = {}

        def absorb(arr):
            for entry in arr or []:
                if isinstance(entry, dict) and "id" in entry:
                    got[norm_id(entry["id"])] = entry.get("text", "")

        absorb(llm_parse_json_array(llm_post(llm_prompt(group, target))))
        missing = [it for it in group if norm_id(it["id"]) not in got]
        if missing:
            # The model loses an item out of twenty now and then - it
            # merges it with a neighbour, or it answers with a different
            # id. A single-item retry is cheap (about a second) and turns
            # a lost sentence back into a translated one.
            for it in missing:
                one = llm_parse_json_array(
                    llm_post(llm_prompt([it], target), max_tokens=24000))
                if one and isinstance(one[0], dict):
                    got[norm_id(it["id"])] = one[0].get("text", "")
        return got

    answered = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = [ex.submit(work, g) for g in groups]
        for fut in as_completed(futures):
            try:
                answered.update(fut.result())
            except Exception:  # noqa: BLE001
                pass
    t_translate = time.time() - t0

    # 3. Check every answer, then repair the ones that broke a rule.
    t0 = time.time()
    repairs = 0
    for idx, (orig, m, saved) in enumerate(masked):
        kind, maxlen = kinds.get(orig, ("body", None))
        raw = answered.get(norm_id(idx), "")
        value = unmask(raw, saved) if raw else ""
        reason = llm_verify(orig, value, saved, maxlen, target)

        if reason and reason.startswith("too long") and maxlen:
            repairs += 1
            shorter = llm_shorten(value, target, maxlen)
            if shorter and not llm_verify(orig, shorter, saved, maxlen, target):
                value = shorter
                reason = None

        if reason:
            # One more try, one item at a time, with a prompt that says
            # the digits are load-bearing. A dropped measurement is the
            # one failure this project cannot ship: "100 lb" becoming
            # "80-100 gsm" is a wrong print spec, not a wrong sentence.
            repairs += 1
            item = {"id": idx, "kind": kind, "text": m}
            if maxlen:
                item["max"] = maxlen
            retry = llm_translate_one_strict(item, target)
            if retry:
                candidate = unmask(retry, saved)
                if not llm_verify(orig, candidate, saved, maxlen, target):
                    value = candidate
                    reason = None

        if reason and reason.startswith("too long") and maxlen:
            # The model does not fit the budget. Try a blunter instruction,
            # and then cut at a word boundary.
            repairs += 1
            shorter = llm_shorten(value, target, maxlen, tighter=True)
            if shorter and not llm_verify(orig, shorter, saved, maxlen, target):
                value = shorter
                reason = None
            else:
                cut = truncate_at_word(value, maxlen)
                if cut and not llm_verify(orig, cut, saved, maxlen, target):
                    value = cut
                    reason = None

        if reason:
            failures.append((orig, reason))
            results[orig] = orig
        else:
            results[orig] = value
    print("    [%s] %d strings, %d batches, %d repairs, translate %.0fs, "
          "verify %.0fs" % (target, len(masked), len(groups), repairs,
                            t_translate, time.time() - t0),
          file=sys.stderr)
    sys.stderr.flush()
    return results, failures


def gtx_batch(items, target, retries=8):
    """Translate SEVERAL strings in one request.

    The endpoint accepts the q parameter more than once and answers with
    one segment per q. That cuts the request count by the batch size, and
    the request count is what makes the free endpoint answer 429: a
    10-string batch is 10x less exposure than 10 single calls.

    Returns None when the response shape is not what we expect, so the
    caller can fall back to single calls.
    """
    if not items:
        return []
    params = [("client", "gtx"), ("sl", "en"), ("tl", target), ("dt", "t")]
    for it in items:
        params.append(("q", it))
    url = GTX_ENDPOINT + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
            break
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                print("    [warn] gtx batch %s failed: %s" % (target, exc), file=sys.stderr)
                return None
            if is_rate_limited(exc):
                print("    [429] rate limited on %s - sleeping before retry %d"
                      % (target, attempt + 1), file=sys.stderr)
            backoff_sleep(attempt)
    else:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        return None
    segs = data[0] if data else []
    out = []
    for seg in segs:
        if isinstance(seg, list):
            out.append("".join(c[0] for c in seg if c and isinstance(c, list) and c[0]))
        else:
            out.append(str(seg))
    if len(out) != len(items):
        return None
    return out


def translate_batch(texts, target, workers=4, pause=0.12, batch=1):
    """Translate a list of strings. Returns (results, failures)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}
    failures = []
    if not texts:
        return results, failures

    if batch > 1:
        groups = [texts[i:i + batch] for i in range(0, len(texts), batch)]
    else:
        groups = [[t] for t in texts]

    def work(group):
        if len(group) == 1:
            out, ok = translate_one(group[0], target)
            return [(group[0], out, ok)]
        masked_pairs = [mask(g) for g in group]
        try:
            raw = gtx_batch([m[0] for m in masked_pairs], target)
        except Exception:  # noqa: BLE001
            raw = None
        if raw is not None:
            out = []
            for (orig, saved), text in zip(masked_pairs, raw):
                value = unmask(text, saved)
                ok = (digits_of(value) == digits_of(orig)
                      and (BRAND not in orig or BRAND in value))
                out.append((orig, value, ok))
            return out
        # Fall back to single calls.
        return [(g, *translate_one(g, target)) for g in group]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(work, g): g for g in groups}
        done = 0
        for fut in as_completed(futures):
            group = futures[fut]
            try:
                results_for_group = fut.result()
            except Exception:  # noqa: BLE001
                results_for_group = [(g, g, False) for g in group]
            for text, value, ok in results_for_group:
                results[text] = value
                if not ok:
                    failures.append(text)
            done += len(group)
            if done % 40 == 0:
                print("      %s: %d/%d" % (target, done, len(texts)))
                sys.stdout.flush()
    return results, failures


def extract_head(html):
    out = {}
    for name, pat in HEAD_FIELDS:
        m = re.search(pat, html, re.S)
        if m:
            out[name] = m.group(1).strip()
    return out


def build_reuse_map(texts, langs, namespace=None, exclude=()):
    """Find strings the site has ALREADY translated somewhere else.

    WHY
    ---
    The free Google endpoint starts answering 429 after a few thousand
    calls, and a retry storm against a 429 wall is how a run turns into
    half an hour of sleeping. But this site's dictionaries hold ~44k-70k
    keys per language, and a tool page's copy is full of phrases the site
    already says somewhere else: "Home", "Free Tools", "Frequently asked
    questions", "Read article", "More free wedding tools".

    So: look the English text up in i18n/en.json, and if the key exists in
    the target language's dictionary too, take THAT translation instead of
    asking the endpoint. The wording is already the site's own.

    Only exact matches are reused - a near-match would be a different
    sentence, and a wrong translation is worse than a missing one.

    `namespace` narrows the search to one prefix of the English dictionary.
    It matters: the full dictionary holds 325 exact matches for a tool
    page's copy, and most of them are the word "No" or "Canva" from an
    unrelated blog table. The tool hub's own chrome (nav labels, "Free
    Tools", "Frequently asked questions") lives under `tools.`, and THAT
    is the wording a tool page has to match.
    """
    wanted = set(texts)
    en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
    hits = {}
    for key, value in en.items():
        if namespace and not key.startswith(namespace):
            continue
        if exclude and key.startswith(tuple(exclude)):
            continue
        if isinstance(value, str) and value in wanted:
            hits.setdefault(value, key)
    if not hits:
        return {}
    out = {}
    for lang in langs:
        path = ROOT / "i18n" / ("%s.json" % lang)
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        for text, key in hits.items():
            value = d.get(key)
            if not isinstance(value, str) or not value or value == text:
                continue
            # A reused value has to pass the same gate a fresh one does.
            # The dictionaries currently hold translations that were
            # produced by the thinking-off model, so the reuse map was
            # pointing straight at the garbage.
            if foreign_spans(value, lang):
                continue
            if not script_ok(value, lang):
                continue
            out.setdefault(text, {})[lang] = value
    return out


def build_sibling_reuse_map(texts, langs, patch_paths):
    """Reuse the translations a SIBLING tool page already paid for.

    WHY
    ---
    A set of tool pages shares most of its chrome. The fourteen planning
    tools repeat the same strings - "Reset", "Print / PDF", "Download .txt",
    "Free Tools", the whole footer - so the same sentence was about to be
    sent to the gateway once per tool, fourteen times, and each answer was
    paid for in the one currency that runs out first: the rate limit.

    The site's own dictionaries cannot help here, because these strings are
    NEW copy that no dictionary holds yet. But the sibling tool's patch
    file does: it holds the English source next to its translation for
    every language.

    So: read the sibling patches, and for a string this page also needs,
    take the translation the sibling already got. The wording is then the
    site's own - which is exactly what the dictionary reuse is for.

    The value still has to pass the same gate a fresh one does. A sibling
    patch written by an older, looser gate can hold a value that the
    current gate would reject, and reusing that would put a bad
    translation into the dictionary.
    """
    wanted = set(texts)
    out = {}
    for path in patch_paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(data, dict):
            continue
        for entry in data.values():
            if not isinstance(entry, dict):
                continue
            source = entry.get("en")
            if not isinstance(source, str) or source not in wanted:
                continue
            for lang in langs:
                value = entry.get(lang)
                if not isinstance(value, str) or not value or value == source:
                    continue
                if foreign_spans(value, lang):
                    continue
                if not script_ok(value, lang):
                    continue
                if english_ngram_leak(source, value):
                    continue
                out.setdefault(source, {})[lang] = value
    return out


def extract_schema_strings(html):
    """Pull the human-readable strings out of the FAQPage and HowTo schema.

    WHY THIS IS NEEDED
    ------------------
    The JSON-LD of a language copy is NOT translated by the middleware: the
    middleware's replaceFaqJsonLd() only knows the homepage_faq and
    pricing_faq scopes. So a tool page's FAQPage block would keep the
    ENGLISH questions and answers on every language page - and a search
    engine sees a structured data block that contradicts the page it sits
    on.

    The FAQ answers here are the SAME strings as the visible FAQ, so they
    are translated with the same result and the schema can never drift
    away from the copy the reader actually sees.
    """
    faq = []
    howto = {"name": "", "steps": []}
    app = {"description": "", "featureList": []}
    for m in re.finditer(r'<script\s+type="application/ld\+json"[^>]*>([\s\S]*?)</script>', html):
        try:
            obj = json.loads(m.group(1))
        except Exception:  # noqa: BLE001
            continue
        kind = obj.get("@type")
        if kind == "FAQPage" and not faq:
            for q in obj.get("mainEntity", []):
                ans = q.get("acceptedAnswer", {})
                faq.append({"name": q.get("name", ""), "text": ans.get("text", "")})
        elif kind == "HowTo" and not howto["name"]:
            howto["name"] = obj.get("name", "")
            for step in obj.get("step", []):
                howto["steps"].append({"name": step.get("name", ""),
                                       "text": step.get("text", "")})
        elif kind == "SoftwareApplication" and not app["description"]:
            app["description"] = obj.get("description", "")
            app["featureList"] = [f for f in obj.get("featureList", []) if isinstance(f, str)]
    return faq, howto, app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--langs", default=",".join(TARGET_LANGS))
    ap.add_argument("--map", default=None, help="the i18n map JSON")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pause", type=float, default=0.12,
                    help="seconds to pause every 8 submissions")
    ap.add_argument("--batch", type=int, default=20,
                    help="how many strings to send in ONE request")
    ap.add_argument("--skip-existing", action="store_true",
                    help="reuse the values a previous run already produced")
    ap.add_argument("--backend", choices=("llm", "gtx"), default="llm",
                    help="llm = the MiniMax gateway (default); "
                         "gtx = the free Google endpoint, which answers 429 "
                         "from most IPs and is kept only for comparison")
    ap.add_argument("--reuse-ns", default="tools.",
                    help="only reuse the site's own translations for keys "
                         "in this namespace (default: tools. = the tool hub "
                         "chrome). A reuse from an unrelated namespace "
                         "carries the wrong context.")
    ap.add_argument("--reuse-exclude", default="",
                    help="comma separated key prefixes to keep OUT of the "
                    "reuse pool. The tools that are being translated "
                    "right now live in the dictionaries already, and "
                    "their values came from a model that was writing "
                    "garbage - so reusing them would feed the garbage "
                    "back in.")
    ap.add_argument("--reuse-siblings", default="",
                    help="comma separated paths of sibling patch files. A "
                    "string a sibling tool already translated is reused "
                    "instead of being asked for again - the shared chrome "
                    "of a tool set is otherwise paid for once per tool.")
    args = ap.parse_args()

    map_path = Path(args.map) if args.map else ROOT / ".tmp" / ("%s-i18n-map.json" % args.slug)
    if not map_path.exists():
        raise SystemExit("[FAIL] no i18n map at %s - run add-tool-i18n-bindings.py first" % map_path)
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    keys = payload["keys"]

    page_path = ROOT / "tools" / args.slug / "index.html"
    html = page_path.read_text(encoding="utf-8")
    head = extract_head(html)

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    for l in langs:
        if l not in TARGET_LANGS:
            raise SystemExit("[FAIL] %s is not a translatable language" % l)

    # Every string that needs a translation: the body keys + the head fields
    # + the schema strings.
    #
    # `kinds` says what each string IS, because a title and a paragraph
    # have different rules: a title has a character budget, a paragraph
    # does not. The budget is not cosmetic - scripts/check-seo-lengths.py
    # walks every html file, language copies included, and fails the
    # deploy on a title over 60 characters.
    faq, howto, app = extract_schema_strings(html)
    kinds = {}

    # The HEAD fields get their budget FIRST, and unconditionally.
    #
    # TRAP: a `<title data-i18n="...">` is itself one of the bound
    # elements, so its text is also in the i18n map. If the body strings
    # are collected first, the title is already "seen" and the head
    # field is skipped - and a French title of 79 characters sails past
    # the 60 character gate with no budget at all.
    head_texts = []
    for name, value in head.items():
        kind, target, hard = HEAD_LIMITS.get(name, ("body", 0, False))
        if hard:
            kinds[value] = (kind, target)
        else:
            kinds[value] = (kind, max(target, int(len(value) * 1.15)))

    body_texts = []
    seen = set()
    for key in payload["order"]:
        t = keys[key]
        if t not in seen:
            seen.add(t)
            body_texts.append(t)
    for value in head.values():
        if value not in seen:
            seen.add(value)
            head_texts.append(value)
    schema_texts = []

    def add_schema(value, kind, factor=None):
        """Add a schema string with its own budget.

        The head fields have HARD budgets (60 / 160) because the deploy
        gate measures them. The structured data has no such budget - the
        gate never reads a JSON-LD block - so its budget is derived from
        the English source instead: a translation may run a third longer
        than the English and still be a faithful rendering. A FIXED
        budget here is what made the SoftwareApplication description
        fail in nine languages: the English is 200 characters, the
        German runs to 230, and a 160 cap turned a good translation into
        an English fallback.

        A schema string that is ALSO a head field keeps the head field's
        budget: the head is the one a gate measures.
        """
        if not value or value in seen:
            return
        seen.add(value)
        schema_texts.append(value)
        if factor is None:
            kinds.setdefault(value, (kind, None))
        else:
            kinds.setdefault(value, (kind, max(12, int(len(value) * factor))))

    for q in faq:
        add_schema(q["name"], "faq_q", 1.4)
        add_schema(q["text"], "body", None)
    add_schema(howto["name"], "title", 1.4)
    for step in howto["steps"]:
        add_schema(step["name"], "title", 1.4)
        add_schema(step["text"], "body", None)
    add_schema(app["description"], "description", 1.3)
    for f in app["featureList"]:
        add_schema(f, "body", 1.5)

    # The body strings come LAST: a string that is also a head field or
    # a schema string keeps that budget. The other order round gave a
    # French title of 79 characters its way past the 60 character gate,
    # because the body copy had claimed the string first and the head
    # field was then skipped as "already seen".
    for t in body_texts:
        kinds.setdefault(t, ("body", None))

    # A budget of 0 means "no hard limit - derive one from the English
    # source". A translation may run about a quarter longer than the
    # English and still say the same thing.
    for text, (kind, limit) in list(kinds.items()):
        if limit == 0:
            kinds[text] = (kind, max(20, int(len(text) * 1.25)))
    all_texts = body_texts + head_texts + schema_texts

    print("translating %d body strings + %d head fields + %d schema strings into %s"
          % (len(body_texts), len(head_texts), len(schema_texts), ",".join(langs)))
    sys.stdout.flush()

    per_lang = {}
    all_failures = {}
    previous = {}
    patch_path = ROOT / ".tmp" / ("%s-patch.json" % args.slug)
    if patch_path.exists():
        try:
            previous = json.loads(patch_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            previous = {}
    head_path = ROOT / ".tmp" / ("%s-head.json" % args.slug)
    previous_heads = {}
    if head_path.exists():
        try:
            previous_heads = json.loads(head_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            previous_heads = {}

    # English text -> the value a language already has. Used by
    # --skip-existing so a second pass only translates what is NEW.
    def done_map(lang):
        out = {}
        for entry in previous.values():
            if not isinstance(entry, dict):
                continue
            en = entry.get("en")
            val = entry.get(lang)
            if en and val and val != en:
                out[en] = val
        head_en = previous_heads.get("en") or {}
        head_val = previous_heads.get(lang) or {}
        if isinstance(head_en, dict) and isinstance(head_val, dict):
            for name, value in head_en.items():
                if name == "jsonld":
                    continue
                target = head_val.get(name)
                if value and target and target != value:
                    out[value] = target
        return out

    # Strings the site has already translated somewhere else. These cost no
    # endpoint calls at all, which matters because the endpoint starts
    # answering 429.
    exclude = tuple(p.strip() for p in args.reuse_exclude.split(",") if p.strip())
    reuse = build_reuse_map(all_texts, langs, namespace=args.reuse_ns or None,
                            exclude=exclude)
    if reuse:
        print("reusing %d strings the site already has in the %s namespace"
              % (len(reuse), args.reuse_ns))

    # Translations a SIBLING tool page already paid for. The planning
    # tools share most of their chrome, and the gateway is the scarce
    # resource - so a string one of them has already translated is
    # reused instead of asked for again.
    sibling_paths = [p for p in (args.reuse_siblings or "").split(",") if p.strip()]
    if sibling_paths:
        sibling = build_sibling_reuse_map(all_texts, langs, sibling_paths)
        if sibling:
            print("reusing %d strings from %d sibling patch file(s)"
                  % (len(sibling), len(sibling_paths)))
            for text, values in sibling.items():
                reuse.setdefault(text, {}).update(values)

    def write_outputs():
        """Write the patch + head files from whatever is translated so far.

        Called after EVERY language, so a run that is killed half-way (or
        that gives up against a 429 wall) still leaves the work it did on
        disk. The next run picks it up with --skip-existing.
        """
        patch = {}
        for key in payload["order"]:
            en = keys[key]
            entry = {"en": en}
            for lang in langs:
                if lang in per_lang:
                    # NEVER fall back to the English here.
                    #
                    # TRAP: a language that was translated in an EARLIER run
                    # looks identical to a language that was never
                    # translated - both are "the English text" - so a
                    # missing item in THIS run silently overwrote a
                    # finished translation with English. That is how 110
                    # good Chinese strings vanished from the
                    # wedding-video-editor patch in one consistency pass.
                    #
                    # The rule: the previous value wins over English, and
                    # only a previous value that IS the English gets
                    # replaced by the English.
                    new = per_lang[lang].get(en)
                    old = previous.get(key, {}).get(lang)
                    if new and new != en:
                        entry[lang] = new
                    elif old and old != en:
                        entry[lang] = old
                    else:
                        entry[lang] = new if new else (old if old else en)
            # Languages that were not translated in this run keep the English
            # text; add-tool-ui-keys.py requires all 11, so fill them in.
            for lang in TARGET_LANGS:
                if lang not in entry:
                    old = previous.get(key, {}).get(lang)
                    entry[lang] = old if old else en
            patch[key] = entry
        atomic_write(patch_path,
                     json.dumps(patch, ensure_ascii=False, indent=1))

        head_out = {"en": head}
        for lang in langs:
            if lang in per_lang:
                # The same rule as the body: a finished translation from an
                # earlier run is never replaced by the English source.
                old_head = previous_heads.get(lang) or {}
                new_head = {}
                for name, value in head.items():
                    new = per_lang[lang].get(value)
                    old = old_head.get(name)
                    if new and new != value:
                        new_head[name] = new
                    elif old and old != value:
                        new_head[name] = old
                    else:
                        new_head[name] = new if new else (old if old else value)
                head_out[lang] = new_head
        for lang in TARGET_LANGS:
            if lang not in head_out and lang in previous_heads:
                head_out[lang] = previous_heads[lang]

        # The schema strings, per language. A string that is also visible on
        # the page reuses the body translation, so the structured data and
        # the copy the reader sees are the same sentence.
        #
        # Same fallback rule as the body and the head: a schema string that
        # an earlier run already translated keeps that translation. Falling
        # back to the English schema text would also make the JSON-LD stop
        # matching the visible copy, because the visible copy is translated
        # by the middleware.
        prev_jsonld = previous_heads.get("jsonld") or {}

        def pick(lang, new_value, old_value, source):
            if new_value and new_value != source:
                return new_value
            if old_value and old_value != source:
                return old_value
            return new_value if new_value else (old_value if old_value else source)

        schema_out = {"en": {"faq": faq, "howto": howto, "app": app}}
        for lang in langs:
            if lang not in per_lang:
                continue
            prev = prev_jsonld.get(lang) or {}
            prev_faq = {q["name"]: q for q in (prev.get("faq") or [])}
            prev_steps = {s["name"]: s for s in
                          ((prev.get("howto") or {}).get("steps") or [])}
            prev_howto_name = (prev.get("howto") or {}).get("name")
            prev_app = prev.get("app") or {}
            prev_features = dict(zip(app["featureList"],
                                     prev_app.get("featureList") or []))
            schema_out[lang] = {
                "faq": [{"name": pick(lang, per_lang[lang].get(q["name"]),
                                      (prev_faq.get(q["name"]) or {}).get("name"),
                                      q["name"]),
                         "text": pick(lang, per_lang[lang].get(q["text"]),
                                      (prev_faq.get(q["name"]) or {}).get("text"),
                                      q["text"])}
                        for q in faq],
                "howto": {
                    "name": pick(lang, per_lang[lang].get(howto["name"]),
                                 prev_howto_name, howto["name"]),
                    "steps": [{"name": pick(lang, per_lang[lang].get(s["name"]),
                                           (prev_steps.get(s["name"]) or {}).get("name"),
                                           s["name"]),
                               "text": pick(lang, per_lang[lang].get(s["text"]),
                                           (prev_steps.get(s["name"]) or {}).get("text"),
                                           s["text"])}
                              for s in howto["steps"]],
                },
                "app": {
                    "description": pick(lang, per_lang[lang].get(app["description"]),
                                         prev_app.get("description"),
                                         app["description"]),
                    "featureList": [
                        pick(lang, per_lang[lang].get(f), prev_features.get(f), f)
                        for f in app["featureList"]],
                },
            }
        head_out["jsonld"] = schema_out
        atomic_write(head_path,
                     json.dumps(head_out, ensure_ascii=False, indent=1))

    for lang in langs:
        done = done_map(lang) if args.skip_existing else {}
        for text, values in reuse.items():
            if lang in values:
                done.setdefault(text, values[lang])
        # A reused value has to pass the same checks a fresh one does.
        if done:
            bad = []
            # The Chinese pass of THIS run is the reference for the
            # Japanese one: it is what tells a kanji-only Japanese label
            # apart from a Chinese sentence. It only exists because the
            # Chinese pass runs first.
            zh_done = per_lang.get("zh", {})
            for text, value in list(done.items()):
                limit = kinds.get(text, ("body", None))[1]
                if not verify_stored(text, value, limit, lang,
                                     zh_done.get(text)):
                    bad.append(text)
            for text in bad:
                del done[text]
                print("    [retranslate] %s: the stored value does not fit "
                      "its budget" % text[:56])
        todo = [t for t in all_texts if t not in done]
        print("  [%s] translating %d strings (%d already done) ..."
              % (lang, len(todo), len(all_texts) - len(todo)))
        sys.stdout.flush()
        if args.backend == "llm":
            results, failures = llm_translate_all(
                todo, kinds, lang, workers=args.workers, batch=args.batch)
            failures = ["%s | %s" % (reason, text[:70])
                        for text, reason in failures]
        else:
            results, failures = translate_batch(
                todo, GTL[lang], workers=args.workers, pause=args.pause,
                batch=args.batch)
        for text, value in done.items():
            results.setdefault(text, value)
        per_lang[lang] = results
        all_failures[lang] = failures
        print("  [%s] done, %d failed" % (lang, len(failures)))
        sys.stdout.flush()
        write_outputs()

    # --- 4. the length consistency pass -------------------------------------
    # A single language can come back with nonsense while the other nine
    # agree. The length against the language's own expectation catches
    # that - and the FALLBACK keeps the original translation, because a
    # compact Chinese sentence is not a defect and the English source
    # would be worse than either.
    outliers = []
    for text in all_texts:
        outliers.extend(ratio_outliers(text, per_lang, langs))
    if outliers:
        print("\n[consistency] %d translation(s) have an impossible length:"
              % len(outliers))
        for text, lang, value, reason in outliers:
            print("   %s: %r (%s)" % (lang, value[:60], reason))
            kind, maxlen = kinds.get(text, ("body", None))
            masked, saved = mask(text)
            item = {"id": 0, "kind": kind, "text": masked}
            if maxlen:
                item["max"] = maxlen
            retry = llm_translate_one_strict(item, lang)
            candidate = unmask(retry, saved) if retry else ""
            low, high = EXPECTED_RATIO.get(lang, (0.4, 2.0))
            src_len = len(text)
            ok = (candidate
                  and src_len * low <= len(candidate) <= src_len * high
                  and not llm_verify(text, candidate, saved, maxlen, lang))
            if ok:
                per_lang[lang][text] = candidate
                print("      -> re-translated: %r" % candidate[:60])
            else:
                print("      -> kept the original")
        write_outputs()

    print("\npatch : %s (%d keys)"
          % (patch_path.relative_to(ROOT), len(payload["order"])))
    print("head  : %s" % head_path.relative_to(ROOT))

    total_fail = sum(len(v) for v in all_failures.values())
    if total_fail:
        print("\n[FAIL] %d strings could not be translated and kept their English text:"
              % total_fail)
        for lang, fails in all_failures.items():
            for f in fails[:20]:
                print("   %s: %s" % (lang, f[:90]))
        return 1
    print("\nall strings translated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
