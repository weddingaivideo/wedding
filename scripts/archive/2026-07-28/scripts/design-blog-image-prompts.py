"""
Design image prompts for all blog articles.

For each article:
- 1 hero prompt (16:9) for /images/blog/hero/<slug>.jpg
- 5 inline prompts (16:9) for /images/blog/inline/<slug>-<n>.jpg
  — derived from the article's H2/H3 subheadings, prioritized by relevance

Prompts aim for a consistent visual style across the blog:
"WeddingAI cinematic still" — soft natural light, shallow depth of field,
warm palette, professional cinematography. Each prompt also includes a
specific subject derived from the article content so the images are
content-relevant (not generic stock wedding photos).

Output: scripts/blog-image-prompts.json
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
OUT = ROOT / "scripts" / "blog-image-prompts.json"

# Visual style anchors — every prompt gets one of these wrappers.
STYLE_HERO = (
    "Cinematic wedding still photograph, soft golden-hour natural light, "
    "shallow depth of field, professional 35mm film look, warm ivory and "
    "champagne palette, emotionally evocative, 16:9 aspect ratio, "
    "editorial magazine quality, no text no watermark no logos"
)
STYLE_INLINE = (
    "WeddingAI cinematic still, soft natural light, shallow depth of field, "
    "warm film tones, professional cinematography, 16:9 aspect ratio, "
    "no text no watermark no logos"
)


def parse_fm(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()
    meta = {}
    for line in fm.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
        else:
            meta[key] = val
    return meta


def extract_subheadings(body: str, max_n: int = 5) -> list[str]:
    """Return up to max_n H2/H3 subheadings, skipping the first H1 (the article title)."""
    subs = []
    h1_seen = False
    for line in body.splitlines():
        m = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if not m:
            continue
        level = len(m.group(1))
        text = re.sub(r"\*+|`", "", m.group(2)).strip()
        if level == 1 and not h1_seen:
            h1_seen = True
            continue
        if level in (2, 3):
            subs.append(text)
        if len(subs) >= max_n:
            break
    return subs


def slug_topic_to_visual(topic: str) -> str:
    """Turn a subheading like 'How AI Frame Interpolation Works' into a
    concrete photographic subject suitable for image-synthesis.

    The goal is to map abstract subheadings to a tangible visual that
    is unambiguous to an image model. We bias toward people + weddings
    + tangible objects so the result looks like a wedding photo, not
    a generic stock illustration.
    """
    t = topic.lower()
    # 1) Specific known topic expansions
    expansions = [
        # restoration — top of the list since many articles are about this
        (r"\brestor|repair|recover|damag|legacy\b",
         "split frame: left side faded vintage wedding photo, right side restored color version, soft editorial light"),
        (r"\b(vhs|tape|cassette|hi8|mini-dv|mini dv|8mm|film reel)\b",
         "vintage analog magnetic tape cassette on a wooden table, soft window light, shallow depth of field"),
        # AI / frame interpolation / slow motion
        (r"\b(slow[- ]?motion|frame interpolation|ai upscal|upscal|240fps|120fps|60fps)\b",
         "a wedding couple sharing their first dance, motion-blurred and crisp in same frame, cinematic slow motion still"),
        # AI video generator / generative — must come BEFORE the generic "wedding video" pattern
        (r"\bai\b.*\b(generat|film|generative|video generator)\b",
         "a glowing laptop screen showing AI video generation interface, soft purple and teal ambient light"),
        # trailer / cinematic
        (r"\b(cinematic|trailer|hollywood)\b",
         "wedding couple in dramatic golden-hour backlight, hair blowing, cinematic color grade"),
        # family tribute / memorial
        (r"\b(memor|tribute|honor|honour|parent|deceased|loved one|passe[sd])\b",
         "a softly lit wedding photo frame on a mantle, single warm candle, ethereal glow"),
        # remote family / video message
        (r"\b(remote family|virtual|long[- ]?distance|video message|message)\b",
         "a laptop screen showing a smiling grandparent, the laptop on a wedding table, warm light"),
        # multilingual / dubbing / subtitles
        (r"\b(multilingual|translation|subtitle|dub|hindi|spanish|french|chinese|korean|japanese|language)\b",
         "wedding reception table with multilingual welcome signs, soft bokeh of multi-language scripts"),
        # cartoon / ghibli / animated / anime
        (r"\b(cartoon|animated|animation|anime|ghibli|illustration|illustrat)\b",
         "a wedding couple rendered in soft Studio Ghibli-inspired watercolor animation style, cherry blossoms"),
        # pet / dog / cat
        (r"\b(pet|dog|cat|puppy|kitten|golden retriever)\b",
         "an adorable golden retriever wearing a wedding collar with a bow tie, soft light, shallow DOF"),
        # drone / aerial
        (r"\b(drone|aerial|overhead)\b",
         "aerial top-down view of a wedding ceremony in a vineyard, drone photography"),
        # microphone / audio / sound
        (r"\b(audio|sound|microphone|music|song|track|background noise|noise reduction)\b",
         "close-up of a wedding microphone against soft stage lights, shallow depth of field"),
        # colorize / black-and-white
        (r"\b(black[- ]?and[- ]?white|colorize|colour|coloris|sepia)\b",
         "split-screen wedding photo: left side vintage black-and-white, right side softly colorized"),
        # caption / subtitling
        (r"\b(caption|sub[- ]??titl)\b",
         "wedding video frame with elegant white serif captions at the bottom, cinematic still"),
        # social / tiktok / reel / instagram
        (r"\b(tiktok|reel|instagram|social media|viral|short[- ]?form)\b",
         "smartphone screen displaying a vertical wedding video, hand holding phone, bokeh wedding reception in background"),
        # memes / gifs
        (r"\b(meme|gif|reaction|funny)\b",
         "wedding guests laughing in slow motion, champagne spray, candid fun moment"),
        # vow renewal / anniversary
        (r"\b(vow renewal|anniversary|re[- ]?new|second ['\u2019]?i do)\b",
         "a couple renewing vows under a flower arch at golden hour, soft intimate moment"),
        # same-sex / lgbtq
        (r"\b(same[- ]?sex|lgbtq|queer|pride|gay|lesbian)\b",
         "two grooms holding hands at a wedding altar, joyful tears, rainbow confetti"),
        # micro / elopement / intimate
        (r"\b(micro|elopement|intimate|tiny)\b",
         "an intimate elopement ceremony on a cliffside at sunset, just the couple and an officiant"),
        # destination
        (r"\b(destination|beach|italy|paris|tropical|abroad|overseas|international)\b",
         "a destination wedding ceremony on a Mediterranean coastal terrace, turquoise sea, golden hour"),
        # christmas / holiday
        (r"\b(christmas|holiday|winter|snow)\b",
         "a winter wedding ceremony with snow falling softly, warm fairy lights, evergreen garlands"),
        # spring
        (r"\b(spring|blossom|cherry|tulip)\b",
         "a spring wedding under a tunnel of cherry blossoms, soft pink petals falling"),
        # summer / outdoor / sun
        (r"\b(summer|sun|outdoor|beach)\b",
         "a bright summer outdoor wedding ceremony, golden grass meadow, lens flare"),
        # how long / length
        (r"\b(length|long|duration|how long|minutes?)\b",
         "a vintage film clapperboard on a wedding table, soft bokeh of bride and groom in background"),
        # share / send
        (r"\b(share|send|deliver|large file|cloud)\b",
         "a smartphone screen showing a wedding video being uploaded to a cloud service, hand holding phone"),
        # photo slideshow
        (r"\b(slideshow|photo montage|montage|photo album)\b",
         "an open wedding photo album on a wooden table, soft window light, shallow depth of field"),
        # raw footage
        (r"\b(raw footage|raw video|unfinished|unedited)\b",
         "a hard drive labeled 'wedding raw footage' on a desk, soft moody side light"),
        # cost / price
        (r"\b(cost|price|pricing|budget|cheap|affordable|expensive|save|money)\b",
         "a laptop screen showing a price list / invoice, wedding-related line items, soft warm light"),
        # photo / from photos / photo-to-video — must come BEFORE generic "wedding video"
        (r"\b(from photos|photo[- ]?to[- ]?video|photo slideshow|stills|still photos)\b",
         "a stack of polaroid wedding photos fanning out on a wooden table, warm light"),
        # video vs photo / video vs photo — BEFORE videographer
        (r"\b(video vs|video versus|video or)\b",
         "split frame: left side a still wedding photo print, right side a wedding video playing on a tablet"),
        # generic "wedding video" — kept late so more specific ones win
        (r"\bwedding video\b",
         "a bride and groom sharing a quiet moment during a cinematic wedding video shoot"),
        # compare / vs
        (r"\b(vs\.?|versus|compare|comparison)\b",
         "split frame: left side traditional videographer with shoulder-mounted camera, right side modern AI editing software on a laptop"),
        # videographer
        (r"\b(videographer|hire|choose|book|select)\b",
         "a wedding videographer with a cinema camera on a gimbal, shooting a couple during golden hour"),
        # format / codec / resolution
        (r"\b(format|codec|resolution|mp4|mov|4k|hd)\b",
         "stacked video tape formats (VHS, MiniDV, SD card) on a table, soft editorial still life"),
        # choosing / planning / timeline / when
        (r"\b(timeline|planning|when to|schedule|day[- ]?of)\b",
         "an open leather-bound wedding planner on a table, with a pen, golden-hour window light"),
        # meme & GIF generator
        (r"\b(generator|catalog|template)\b",
         "a tablet screen showing a meme template library, hand scrolling, bokeh wedding background"),
        # zoom / virtual / live
        (r"\b(zoom|live[- ]?stream|live edit|live[- ]?comment)\b",
         "a laptop screen showing a live video stream of a wedding ceremony, hand resting next to it"),
        # stabilization / shaky
        (r"\b(shake|shaky|stabili|steady|gimbal)\b",
         "a wedding videographer with a gimbal-mounted cinema camera, smooth tracking shot composition"),
        # copyright-free music
        (r"\b(royalty[- ]?free|copyright[- ]?free|library music|stock music|free music)\b",
         "vintage vinyl records stacked with a wedding photo on top, soft warm light"),
        # gift / surprise
        (r"\b(gift|surprise|anniversary gift)\b",
         "a beautifully wrapped wedding anniversary gift box with a satin ribbon, soft bokeh"),
        # success story / review / testimonial
        (r"\b(success|review|testimonial|case stud|customer)\b",
         "a wedding photo album open to a happy couple laughing, soft window light, editorial style"),
        # mood/emotion keywords
        (r"\b(emotional impact|impact|emotional)\b",
         "bride wiping a tear during vows, intimate close-up, soft window light"),
        (r"\b(creative expression|expression|creativity)\b",
         "wedding photographer holding a vintage film camera, creative composition"),
        (r"\b(privacy|sharing|share)\b",
         "a couple sharing a private moment at their wedding, blurred guests in background"),
        (r"\b(standing out|unique|stand out)\b",
         "an unconventional wedding setup in an industrial loft, dramatic lighting"),
        (r"\b(participat|pet ring|ring bearer|flower)\b",
         "a small dog carrying a ring pillow down the aisle, candid moment"),
        # 47 specific
        (r"\b(package|premium|standard|basic|\\$\d|\d{3,4})\b",
         "a wedding videographer with a cinema camera on a tripod at golden hour"),
        # closing calls to action
        (r"\b(why|reason|important|essential|key|need)\b",
         "wedding planner pointing at a checklist with the couple, soft bokeh"),
    ]
    for pat, vis in expansions:
        if re.search(pat, t):
            return vis

    # Fallback: extract 2-3 salient nouns from the subheading and
    # build a concrete wedding scene around them.
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
        "with", "how", "what", "why", "when", "where", "your", "you",
        "is", "are", "be", "this", "that", "from", "by", "as", "it",
        "at", "we", "our", "their", "his", "her", "into", "than",
        "very", "more", "most", "first", "next",
    }
    words = [w.strip(".,!?()[]\"'").lower() for w in re.split(r"\s+", topic)]
    nouns = [w for w in words if w and w not in stop and len(w) > 2][:4]
    if nouns:
        return (
            f"a cinematic wedding still showing a bride and groom with "
            f"{', '.join(nouns[:2])} in the scene, soft warm light, "
            f"shallow depth of field, editorial wedding photography"
        )
    return "a cinematic wedding still, soft golden hour light, bride and groom, shallow depth of field"


def design_prompts() -> dict:
    out = {}
    for md in sorted(ARTICLES.glob("*.md")):
        slug = md.stem
        text = md.read_text(encoding="utf-8")
        meta = parse_fm(text)
        # split frontmatter
        body = text
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                body = text[end + 4:]

        primary = meta.get("primary_keyword", "wedding video")
        title = meta.get("title", slug.replace("-", " "))
        category = meta.get("category", "B")

        # Hero prompt — use the primary keyword so it matches the article's
        # search intent, not the (often wordy) title.
        hero_subject = slug_topic_to_visual(primary)
        hero_prompt = f"{hero_subject}, {STYLE_HERO}"

        # Inline prompts — one per top subheading
        subs = extract_subheadings(body, max_n=5)
        # If we have fewer than 5 subheadings, fill from secondary_keywords
        if len(subs) < 5:
            sec = meta.get("secondary_keywords", []) or []
            if isinstance(sec, str):
                sec = [sec]
            for kw in sec:
                if len(subs) >= 5:
                    break
                kw_clean = kw.strip()
                if kw_clean and kw_clean.lower() not in (s.lower() for s in subs):
                    subs.append(kw_clean)
        # Trim to 5
        subs = subs[:5]
        # Pad if still short (shouldn't happen, but be safe)
        while len(subs) < 5:
            subs.append(f"Related concept {len(subs)+1} for '{primary}'")

        inline_prompts = []
        alt_texts = []
        for i, sub in enumerate(subs, start=1):
            subject = slug_topic_to_visual(sub)
            inline_prompts.append(f"{subject}, {STYLE_INLINE}")
            alt_texts.append(f"{sub} — visual illustrating the {sub.lower()} aspect of the article")

        out[slug] = {
            "title": title,
            "primary_keyword": primary,
            "hero": {
                "prompt": hero_prompt,
                "alt": f"{title} — illustrated with a cinematic wedding still",
                "filename": f"images/blog/hero/{slug}.jpg",
            },
            "inline": [
                {
                    "prompt": p,
                    "alt": a,
                    "filename": f"images/blog/inline/{slug}-{i}.jpg",
                }
                for i, (p, a) in enumerate(zip(inline_prompts, alt_texts), start=1)
            ],
        }
    return out


if __name__ == "__main__":
    data = design_prompts()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_heroes = len(data)
    total_inline = sum(len(v["inline"]) for v in data.values())
    print(f"[ok] {OUT.relative_to(ROOT)}")
    print(f"     heroes: {total_heroes}")
    print(f"     inline: {total_inline} (target: {total_heroes*5})")
    # show one example
    sample = list(data.values())[0]
    print(f"\nSample '{list(data.keys())[0]}':")
    print(f"  hero prompt: {sample['hero']['prompt'][:120]}...")
    print(f"  inline[0]:   {sample['inline'][0]['prompt'][:120]}...")
