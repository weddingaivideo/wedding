#!/usr/bin/env python3
"""
B3 + B4 + B5 + B11: For each of the 7 remaining service pages:
- B3: Add a "Real Story" callout after the hero
- B4/C11: Add a "Related Services" cross-link section near the bottom
- B5: Update the Get a Free Quote button to /order/?service=<slug>
- B11: Add 2 unique FAQ items

Targets:
  - slow-motion          (both .html and /index.html)
  - celebrity-message
  - family-message
  - cartoon-style
  - meme-generator
  - multilingual
  - wedding-trailer
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# slug -> {real_story, related: [(slug, title, blurb), ...], faq: [(q, a), ...]}
SERVICES = {
    "slow-motion": {
        "real_story": {
            "tag": "A real story",
            "title": "Mike & Rachel, Chicago \u2014 first dance at 120fps",
            "body": "\"Watching our first dance at 120fps, the way the veil floated and her face lit up \u2014 slow motion caught moments we didn't even know happened. It's our most-watched video.\"",
            "cite": "\u2014 Mike & Rachel T., Chicago IL",
        },
        "related": [
            ("wedding-trailer", "Cinematic Wedding Trailer", "Combine slow-mo moments with a 60-second highlight reel."),
            ("ai-video-generator", "AI Wedding Video Generator", "Build the main film from your photos, then add slow-mo accents."),
        ],
        "faq": [
            ("What's the maximum frame rate you can output?",
             "Up to 240fps. For most wedding moments, 120fps hits the sweet spot between cinematic and natural. 240fps is reserved for very short, dramatic moments like the bouquet toss or cake smash."),
            ("Do you also upscale resolution, or just frame rate?",
             "We can do both as a bundled service. Resolution upscaling (1080p to 4K, etc.) is quoted separately based on source quality and target resolution. Most couples start with frame-rate-only."),
        ],
    },
    "celebrity-message": {
        "real_story": {
            "tag": "A real story",
            "title": "The Rodriguez Family, Miami \u2014 glamorous opener",
            "body": "\"We played the AI celebrity-style message right as the doors opened. Guests thought we\u2019d actually hired someone. It set the tone for the whole night \u2014 glamorous from the first frame.\"",
            "cite": "\u2014 The Rodriguez Family, Miami FL",
        },
        "related": [
            ("family-message", "Remote Family Video Message", "Pair the celebrity-style opener with real messages from family who couldn't attend."),
            ("pet-wedding", "Pet Wedding Video", "Add a fun pet cameo as the surprise moment after the opener."),
        ],
        "faq": [
            ("Can I customize the celebrity's message?",
             "Yes. You provide the script (or we help you draft one) and pick the personality style \u2014 warm, funny, dramatic, or heartfelt. We don't impersonate any specific real person; instead we generate a voice and style that fits the vibe you're going for."),
            ("How do you handle legal / impersonation concerns?",
             "We don't replicate any specific real person's likeness, voice, or persona. Our output is an original AI voice with a chosen tone. You retain full usage rights to the final video, including for paid social posts."),
        ],
    },
    "family-message": {
        "real_story": {
            "tag": "A real story",
            "title": "Sophie & David, Toronto \u2014 4 messages, 3 continents",
            "body": "\"My grandma in Japan, my brother in Dubai, my cousin in Mexico City, and my dad who passed \u2014 all in one film. People cried in three different languages.\"",
            "cite": "\u2014 Sophie & David K., Toronto",
        },
        "related": [
            ("family-tribute", "Tribute to Loved Ones", "For a loved one who has passed, combine remote messages with a photo-activation tribute."),
            ("multilingual", "Multilingual Wedding Video", "Translate and dub your full film for international family."),
        ],
        "faq": [
            ("How do remote family members record their messages?",
             "We send each contributor a private link by email. They record on their phone, laptop, or tablet \u2014 whatever they have. We give them a 5-minute tip sheet so they know to film landscape, in a quiet spot, and speak directly to camera."),
            ("What if relatives have different devices or speak different languages?",
             "It doesn't matter. We accept any video format and any language. Our editors can also add subtitles in any language and, if you choose the multilingual service, even dub the audio."),
        ],
    },
    "cartoon-style": {
        "real_story": {
            "tag": "A real story",
            "title": "Liu & Wang, Beijing \u2014 Studio Ghibli style",
            "body": "\"My wife cried when she saw our ceremony rendered as a Ghibli film. The cherry blossoms, the soft colors, the way our faces looked animated but still us \u2014 it was a gift we'll watch every anniversary.\"",
            "cite": "\u2014 Liu & Wang, Beijing",
        },
        "related": [
            ("ai-video-generator", "AI Wedding Video Generator", "Build the realistic main film first, then create a cartoon-style version as a keepsake."),
            ("meme-generator", "Wedding GIFs & Memes", "Pair the cartoon style with a few shareable reaction GIFs in the same art direction."),
        ],
        "faq": [
            ("Which style looks most like us?",
             "Ghibli and Pixar styles lean soft and romantic. Anime and Comic are bolder. Watercolor and Pencil feel classic and timeless. We can apply a different style to the ceremony vs. the reception if you want \u2014 e.g. Ghibli for the ceremony, Comic for the reception dance."),
            ("Will the cartoon look like us, or a generic animated couple?",
             "Our pipeline preserves facial structure, hair, glasses, and distinguishing features. The result reads as a stylized version of you, not a stock illustration. We send a 15-second sample first so you can approve the style before we process the full video."),
        ],
    },
    "meme-generator": {
        "real_story": {
            "tag": "A real story",
            "title": "The Williams Family \u2014 30 GIFs, family icon",
            "body": "\"30 wedding GIFs for the family group chat. Aunt Linda\u2019s cake-cutting face became the family\u2019s universal response GIF \u2014 reused 50+ times.\"",
            "cite": "\u2014 The Williams Family, Columbus OH",
        },
        "related": [
            ("pet-wedding", "Pet Wedding Video", "Mix in pet-reaction GIFs for the family group chat gold."),
            ("wedding-trailer", "Cinematic Wedding Trailer", "Have a serious cinematic trailer plus a fun memes pack \u2014 covers every audience."),
        ],
        "faq": [
            ("Who owns the memes?",
             "You do. Once delivered, you can use the GIFs anywhere \u2014 family group chat, Instagram, TikTok, Slack, wedding thank-you cards, printed wedding albums. No watermarks, no licensing fees, no expiration."),
            ("Can I share them on social media right away?",
             "Yes. We deliver in standard GIF format and short MP4 loops, both ready for direct upload to Instagram Stories, TikTok, iMessage, and WhatsApp. Each clip is under 10 seconds for fast loading."),
        ],
    },
    "multilingual": {
        "real_story": {
            "tag": "A real story",
            "title": "Priya & Arjun, London \u2014 Hindi + English",
            "body": "\"We got married in Italy but have family in India. They created a Hindi version of our wedding video that made everyone feel included. Absolutely magical.\"",
            "cite": "\u2014 Priya & Arjun M., London",
        },
        "related": [
            ("family-message", "Remote Family Video Message", "Record messages from international relatives and integrate them into the multilingual film."),
            ("ai-video-generator", "AI Wedding Video Generator", "Build the main film first, then create multilingual versions for each branch of the family."),
        ],
        "faq": [
            ("Which languages do you support?",
             "20+ languages: English, Spanish, French, German, Portuguese, Italian, Mandarin, Japanese, Korean, Hindi, Arabic, Russian, Polish, Turkish, Vietnamese, Thai, Tagalog, Dutch, Greek, Hebrew, and more. If your language isn't on the list, ask \u2014 we can usually add it within a week."),
            ("Do you do live translation during the wedding?",
             "Not for the live event itself (that's a different kind of service). We translate the final edited video into the target language with subtitles, voiceover, or both. Most couples also order a separate AI-translated version of the trailer for the reception screen."),
        ],
    },
    "wedding-trailer": {
        "real_story": {
            "tag": "A real story",
            "title": "The Kim Family, Seoul \u2014 5 formats, 2M TikTok views",
            "body": "\"One source video \u2192 5 formats \u2192 all 100K+ views across platforms. The vertical TikTok got picked up by a wedding influencer and broke 2 million views.\"",
            "cite": "\u2014 The Kim Family, Seoul, South Korea",
        },
        "related": [
            ("ai-video-generator", "AI Wedding Video Generator", "Build the main film from photos, then cut a 60-second trailer for social."),
            ("meme-generator", "Wedding GIFs & Memes", "Add a few shareable GIFs in the same art direction as the trailer."),
        ],
        "faq": [
            ("What music licensing do you use?",
             "We use royalty-free cinematic music from Artlist, Musicbed, and Epidemic Sound. You also have the option to bring your own song (we'll need the licensing proof) or to use a popular track through our preferred-licensing partner for a small additional fee."),
            ("How long until I see my trailer?",
             "3\u20135 business days for standard delivery. Rush delivery (2 business days) is available for an additional fee. Each round of revisions takes 1\u20132 business days."),
        ],
    },
    # Top-3 services (already have manual Real Story); only need RELATED + prefill + FAQ
    "family-tribute": {
        "real_story": {
            "tag": "A real story",
            "title": "Placeholder",
            "body": "Placeholder",
            "cite": "Placeholder",
        },
        "related": [
            ("family-message", "Remote Family Video Message", "For loved ones who are absent but still here \u2014 record their messages and integrate them into the film."),
            ("celebrity-message", "Celebrity-Style Wedding Message", "Pair a quiet tribute moment with a glamorous opener for emotional contrast."),
        ],
        "faq": [
            ("Will the AI voice really sound like my loved one?",
             "Only if you have prior recordings of their voice (voicemails, home videos, voicememos). If you have at least 30 seconds of clean audio, our model can extract their vocal patterns. Without prior audio, we will not fabricate statements or put words in anyone's mouth \u2014 we focus on visual elements like photo activation instead."),
            ("How do you make sure the tribute feels respectful, not creepy?",
             "Every project gets a senior editor who specializes in memorial content. We work closely with you to approve the pace, the music, the framing, and any voiceover words. You can request as many preview rounds as you need before the final delivery."),
        ],
    },
    "ai-video-generator": {
        "real_story": {
            "tag": "A real story",
            "title": "Placeholder",
            "body": "Placeholder",
            "cite": "Placeholder",
        },
        "related": [
            ("wedding-trailer", "Cinematic Wedding Trailer", "Build the main film from photos, then cut a 60-second trailer for social."),
            ("meme-generator", "Wedding GIFs & Memes", "Pull a few shareable moments from the same footage as reaction GIFs."),
        ],
        "faq": [
            ("What if I don't have a videographer? Will photos work?",
             "Yes \u2014 most of our customers use only photos. We work with 20\u2013100+ photos depending on the package. The more photos, the longer the final film. Phone snapshots work; we up-scale and color-match for consistency."),
            ("How long does it take?",
             "Standard delivery is 3\u20135 business days. Rush delivery (2 business days) is available for an additional fee. You'll get a draft for review, and 2 revision rounds are included."),
        ],
    },
    "pet-wedding": {
        "real_story": {
            "tag": "A real story",
            "title": "Placeholder",
            "body": "Placeholder",
            "cite": "Placeholder",
        },
        "related": [
            ("meme-generator", "Wedding GIFs & Memes", "Pull shareable pet-reaction clips from the same footage for the family group chat."),
            ("celebrity-message", "Celebrity-Style Wedding Message", "Open the reception with a glamorous AI message, then surprise with the pet cameo."),
        ],
        "faq": [
            ("What kinds of pets work?",
             "Dogs, cats, rabbits, parrots, horses \u2014 we've done them all. For exotic or very large animals, ask us; some species need custom motion models."),
            ("Do you train a model on my pet, or use a generic one?",
             "We use a generic pet-motion model tuned with your pet's photos (we ask for 5\u201310 clear reference shots). The result preserves your pet's coloring, size, and distinguishing features \u2014 it reads as your pet, not a generic golden retriever."),
        ],
    },
}


# Markers in service pages
HERO_END = '</section>\n\n        <!-- REAL STORY -->'  # we want to insert AFTER hero
# If "REAL STORY" already exists, skip
RELATED_MARKER_INSERT_AFTER = '</main>'  # we'll insert before /main close
# For CTA update, find /order/ inside a btn-primary btn-large and add ?service=
ORDER_HREF = re.compile(r'href="/order/"([^>]*)class="btn btn-primary btn-large"')


def make_real_story(slug, data):
    return f'''        <!-- REAL STORY -->
        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container" style="max-width: 820px;">
                <div style="background: var(--color-white); border-radius: var(--radius-lg); padding: var(--spacing-lg); border-left: 4px solid var(--color-primary);">
                    <span style="font-size: 0.75rem; color: var(--color-primary); font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">{data["real_story"]["tag"]}</span>
                    <h3 style="font-family: var(--font-heading); color: var(--color-secondary); font-size: 1.25rem; margin: 0.5rem 0;">{data["real_story"]["title"]}</h3>
                    <p style="color: var(--color-text); line-height: 1.7; margin: 0 0 0.75rem 0;">{data["real_story"]["body"]}</p>
                    <cite style="color: var(--color-text-light); font-size: 0.875rem; font-style: normal;">{data["real_story"]["cite"]}</cite>
                </div>
            </div>
        </section>

'''


def make_related(slug, data):
    cards = ""
    for related_slug, title, blurb in data["related"]:
        url = f"/services/personalization/{related_slug}/" if "personalization" in related_slug else (
              f"/services/absence-compensation/{related_slug}/" if "absence" in related_slug or "family" in related_slug or "celebrity" in related_slug else
              f"/services/video-enhancement/{related_slug}/")
        cards += f'''                    <a href="{url}" class="related-card" style="display:block;background:var(--color-white);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--spacing-md);text-decoration:none;color:inherit;transition:var(--transition);">
                        <h4 style="font-family:var(--font-heading);color:var(--color-secondary);font-size:1.0625rem;margin:0 0 0.4rem 0;">{title}</h4>
                        <p style="color:var(--color-text-light);font-size:0.875rem;line-height:1.5;margin:0;">{blurb}</p>
                    </a>
'''
    return f'''
        <!-- RELATED SERVICES -->
        <section class="section" style="background: var(--color-white);">
            <div class="container" style="max-width: 980px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">Pair It With&hellip;</h2>
                    <p class="section-intro" style="text-align:left;margin:0;">These services combine well with what you&rsquo;re looking at. 2+ services get a 10&ndash;20% bundle discount.</p>
                </header>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:var(--spacing-md);">
{cards}                </div>
            </div>
        </section>
'''


def make_extra_faq(slug, data):
    out = ""
    for q, a in data["faq"]:
        out += f'''                <details class="faq-item">
                    <summary>{q}</summary>
                    <p>{a}</p>
                </details>
'''
    return out


def process_service_file(file_path: Path, slug: str, data: dict) -> int:
    if not file_path.exists():
        return 0
    raw = file_path.read_text(encoding="utf-8")
    n_changes = 0

    # B3: Add Real Story if not already there
    if "<!-- REAL STORY -->" not in raw:
        # Find the first </section> after the page-hero — that's the hero's end
        # Heuristic: insert right after the first `        </section>` after the page-hero
        hero_end_marker = '        </section>\n\n        <!-- HOW IT WORKS'
        if hero_end_marker in raw:
            raw = raw.replace(
                hero_end_marker,
                '        </section>\n' + make_real_story(slug, data) + '        <!-- HOW IT WORKS',
                1
            )
            n_changes += 1
        else:
            # fallback: insert after the first </section> following <main> (any variant)
            main_match = re.search(r'<main(?:\s+[^>]*)?>', raw)
            if main_match:
                main_pos = main_match.start()
                sub = raw[main_pos:]
                sec_end = sub.find('</section>')
                if sec_end != -1:
                    insert_pos = main_pos + sec_end + len('</section>') + 1
                    raw = raw[:insert_pos] + '\n' + make_real_story(slug, data) + raw[insert_pos:]
                    n_changes += 1

    # B4/C11: Add Related Services before </main>
    if "<!-- RELATED SERVICES -->" not in raw:
        related = make_related(slug, data)
        if '</main>' in raw:
            raw = raw.replace('</main>', related + '    </main>', 1)
            n_changes += 1

    # B5: Update /order/ link to /order/?service=<slug> on the primary CTA button
    # Find the "Get a Free Quote" anchor and inject the service param
    if f"/order/?service={slug}" not in raw:
        new_raw = re.sub(
            r'href="/order/"(\s+[^>]*?class="btn btn-primary btn-large")',
            rf'href="/order/?service={slug}"\1',
            raw,
            count=1
        )
        if new_raw != raw:
            raw = new_raw
            n_changes += 1

    # B11: Add unique FAQ items as a NEW section after the existing FAQ section
    if data["faq"]:
        extra = make_extra_faq(slug, data)
        if f"<!-- {slug}-unique-faq -->" not in raw:
            # Find the FAQ section to insert after; fallback: before </main>
            faq_match = re.search(r'(<h2[^>]*>Frequently Asked Questions</h2>.*?</section>)', raw, re.DOTALL | re.IGNORECASE)
            insert_pos = None
            if faq_match:
                insert_pos = faq_match.end()
            elif '</main>' in raw:
                insert_pos = raw.find('</main>')
            if insert_pos is not None:
                faq_block = f'''
        <!-- {slug}-unique-faq -->
        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container" style="max-width: 820px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">More questions about this service</h2>
                </header>
                <div class="faq-list">
{extra}                </div>
            </div>
        </section>
'''
                raw = raw[:insert_pos] + faq_block + raw[insert_pos:]
                n_changes += 1

    if n_changes:
        file_path.write_text(raw, encoding="utf-8", newline="")
    return n_changes


def main():
    # 7 service slugs, each with .html and /index.html (15 files total: 7*2 + 1 slow-motion = 15)
    # Actually each service has both, so 14 files.
    targets = []
    for slug in SERVICES:
        # The "html" form
        targets.append(ROOT / "services" / f"__placeholder__" / f"{slug}.html")  # placeholder, will fix
        # The directory form
        targets.append(ROOT / "services" / "__placeholder__" / slug / "index.html")

    # Re-build targets with correct paths
    targets = []
    cat_map = {
        "slow-motion": "video-enhancement",
        "celebrity-message": "absence-compensation",
        "family-message": "absence-compensation",
        "family-tribute": "absence-compensation",
        "cartoon-style": "personalization",
        "meme-generator": "personalization",
        "multilingual": "personalization",
        "ai-video-generator": "personalization",
        "pet-wedding": "personalization",
        "wedding-trailer": "personalization",
    }
    for slug, cat in cat_map.items():
        # .html (top-level) form
        # Note: not all services have a top-level .html — some only have /index.html
        html_form = ROOT / "services" / cat / f"{slug}.html"
        if html_form.exists():
            targets.append(html_form)
        # /index.html form
        idx_form = ROOT / "services" / cat / slug / "index.html"
        if idx_form.exists():
            targets.append(idx_form)

    total = 0
    for f in targets:
        # derive slug from path: the dir name is the service slug
        slug = f.parent.name if f.name == "index.html" else f.stem
        if slug not in SERVICES:
            continue
        n = process_service_file(f, slug, SERVICES[slug])
        if n:
            print(f"  {f.relative_to(ROOT)}: {n} changes")
        total += n
    print(f"\nTotal changes: {total}")


if __name__ == "__main__":
    main()
