"""
Generate /services/video-enhancement/index.html and /services/personalization/index.html.

The parent category pages previously 404'd (Crawl 2026-08-04). This builds minimal
index.html files for each, using the same nav/footer/JSON-LD scaffolding as the
existing /services/index.html. i18n versions of these new pages are served
automatically by the /xx/* → /:splat 200 rewrite in _redirects.
"""
from pathlib import Path

ROOT = Path(".")

# Common scaffolding: lang list, nav, footer. Mirrors /services/index.html
# (single source of truth so any nav/footer update flows from the same set
# of i18n keys).
LANGS = [
    ("en", "en"),  # x-default handled separately
    ("zh", "zh"),
    ("es", "es"),
    ("fr", "fr"),
    ("de", "de"),
    ("pt", "pt"),
    ("ja", "ja"),
    ("ru", "ru"),
    ("ar", "ar"),
    ("th", "th"),
]

NAV_ITEMS = [
    ("/services/video-enhancement/slow-motion/",      "404.a_text.slow_motion.30129340",        "Slow Motion"),
    ("/services/video-enhancement/vintage-restoration/", "404.a_text.vintage_restoration.91827364",  "Vintage Restoration"),
    ("/services/personalization/wedding-trailer/",   "404.a_text.wedding_trailer.04692297",     "Wedding Trailer"),
    ("/services/personalization/ai-video-generator/","404.a_text.ai_video_generator.39420322",  "AI Video Generator"),
    ("/services/personalization/pet-wedding/",       "404.a_text.pet_wedding.23911820",        "Pet Wedding"),
    ("/services/personalization/multilingual/",      "404.a_text.multilingual.74639147",        "Multilingual"),
    ("/services/personalization/cartoon-style/",     "404.a_text.cartoon_style.16664616",       "Cartoon Style"),
    ("/services/personalization/meme-generator/",    "404.a_text.wedding_memes.22951185",      "Wedding Memes"),
    ("/services/absence-compensation/family-tribute/","404.a_text.family_tribute.39408322",     "Family Tribute"),
    ("/services/absence-compensation/family-message/","404.a_text.family_message.27013166",     "Family Message"),
]

# Service group definitions for the new parent pages.
GROUPS = {
    "video-enhancement": {
        "slug": "video-enhancement",
        "name": "Video Enhancement",
        "i18n_name_key": "search.strong_text.video_enhancement.98039549",
        "h1": "AI Video Enhancement Services",
        "h1_i18n": "services.video-enhancement.h1_text.ai_video_enhancement_services.enh00001",
        "intro": "Restore old footage, add cinematic slow motion, and improve the quality of any wedding video — even from 30 years ago.",
        "intro_i18n": "services.video-enhancement.p_text.intro.enh00001",
        "children": [
            {
                "href": "/services/video-enhancement/slow-motion/",
                "title": "AI Slow Motion Enhancement",
                "title_i18n": "blog.weddingai-video-review.a_text.ai_slow_motion_enhancement.36606060",
                "desc": "Transform standard footage into smooth 60fps+ slow motion.",
                "desc_i18n": "services.p_text.transform_standard_footage_into_smooth_6.78468195",
                "price": "From $99",
                "price_i18n": "services.span_text.from_99.96638139",
                # 1:1 mirror of the gallery case-study video (case-slow-motion-
                # dance-…). Replaces the static catalog-slow-motion.jpg so
                # visitors see the actual rendered slow-motion dip in motion.
                # ?v=4.29 matches gallery/index.html (cache-bust parity).
                "video": {
                    "width": 1376,
                    "height": 768,
                    "poster": "/images/case-slow-motion-dance-poster.webp",
                    "webm": "/images/case-slow-motion-dance.webm?v=4.29",
                    "mp4": "/images/case-slow-motion-dance.mp4?v=4.29",
                    "aria_label": "Maria & David — first dance dip in cinematic 120fps slow motion",
                },
            },
            {
                "href": "/services/video-enhancement/vintage-restoration/",
                "title": "Vintage Restoration",
                "title_i18n": "404.a_text.vintage_restoration.91827364",
                "desc": "Restore and enhance old VHS, Hi8, and film wedding footage.",
                "desc_i18n": "services.video-enhancement.p_text.vintage_desc.enh00002",
                "price": "From $149",
                "price_i18n": "services.span_text.from_149.82399004",
                # 1:1 mirror of the gallery case-study video (case-1987-vhs-
                # restoration-…). Replaces the static wedding-restoration-
                # before-after.png + catalog-vintage-restoration.jpg (which
                # was on the hand-edited main page, not the script) so both
                # pages show the actual 1987 VHS-to-4K before/after loop.
                # NOTE: NO `?v=4.29` query string here — gallery/index.html
                # line 372-373 omits the cache-bust on this video (the only
                # case-study video in gallery that does). Match exactly.
                "video": {
                    "width": 1280,
                    "height": 720,
                    "poster": "/images/case-1987-vhs-restoration-poster.webp",
                    "webm": "/images/case-1987-vhs-restoration.webm",
                    "mp4": "/images/case-1987-vhs-restoration.mp4",
                    "aria_label": "1987 wedding video — VHS to 4K restoration, before and after",
                },
            },
        ],
    },
    "absence-compensation": {
        "slug": "absence-compensation",
        "name": "Absence Compensation",
        "i18n_name_key": "search.strong_text.absence_compensation.22965696",
        "h1": "Absence Compensation Wedding Video Services",
        "h1_i18n": "services.absence-compensation.h1_text.absence_compensation_wedding_video.absent00001",
        "intro": "Make sure no one is missing from your wedding day — include loved ones who can't attend, or honor those who've passed.",
        "intro_i18n": "services.absence-compensation.p_text.intro.absent00001",
        "children": [
            {
                "href": "/services/absence-compensation/family-tribute/",
                "title": "Tribute to Loved Ones",
                "title_i18n": "order.option_text.tribute_to_loved_ones.19174648",
                "desc": "Respectfully include deceased family members in your wedding video.",
                "desc_i18n": "services.p_text.respectfully_include_deceased_family_mem.14848440",
                "price": "From $149",
                "price_i18n": "services.span_text.from_149.82399004",
                # 1:1 mirror of the gallery case-study video (case-johnson-
                # grandpa-voice-…). Replaces the static catalog-family-tribute.jpg
                # so visitors see the actual rendered father-daughter dance +
                # reconstructed-voice moment in motion. ?v=4.29 matches gallery.
                "video": {
                    "width": 1280,
                    "height": 720,
                    "poster": "/images/case-johnson-grandpa-voice-poster.webp",
                    "webm": "/images/case-johnson-grandpa-voice.webm?v=4.29",
                    "mp4": "/images/case-johnson-grandpa-voice.mp4?v=4.29",
                    "aria_label": "The Johnson Family — bride listening to grandfather's reconstructed voice message during father-daughter dance, tears of joy",
                },
            },
            {
                "href": "/services/absence-compensation/family-message/",
                "title": "Remote Family Video Message",
                "title_i18n": "404.a_text.family_message.27013166",
                "desc": "Integrate video messages from family who can't attend in person.",
                "desc_i18n": "services.p_text.integrate_video_messages_from_family_who.96853389",
                "price": "From $149",
                "price_i18n": "services.span_text.from_149.82399004",
                # 1:1 mirror of the gallery case-study video (case-sophie-david-
                # family-messages-…). Replaces the static catalog-family-message.jpg
                # so visitors see the actual rendered remote-call grid in motion.
                # Style attr keeps the video fluid inside the service-sub-card
                # (16:9 aspect + 100% width, no CLS). Matches hand-edit on
                # services/index.html exactly.
                "video": {
                    "width": 1280,
                    "height": 720,
                    "style": "width: 100%; height: auto; display: block; aspect-ratio: 16/9; object-fit: cover;",
                    "poster": "/images/case-sophie-david-family-messages-poster.webp",
                    "webm": "/images/case-sophie-david-family-messages.webm?v=4.29",
                    "mp4": "/images/case-sophie-david-family-messages.mp4?v=4.29",
                    "aria_label": "Remote Family Video Message — wedding couple watching family video call grid from around the world",
                },
            },
        ],
    },
    "personalization": {
        "slug": "personalization",
        "name": "Personalization",
        "i18n_name_key": "search.strong_text.personalization.44366515",
        "h1": "Personalized AI Wedding Video Services",
        "h1_i18n": "services.personalization.h1_text.personalized_ai_wedding_video_serv.pers00001",
        "intro": "Make your wedding video uniquely yours with creative AI-powered options — from cinematic trailers to multilingual dubbing.",
        "intro_i18n": "services.personalization.p_text.intro.pers00001",
        "children": [
            {
                "href": "/services/personalization/ai-video-generator/",
                "title": "AI Wedding Video Generator",
                "title_i18n": "order.option_text.ai_wedding_video_generator.54212344",
                "desc": "Turn your photos into a cinematic wedding film using AI.",
                "desc_i18n": "services.p_text.turn_your_photos_into_a_cinematic_weddin.02467471",
                "price": "From $199",
                "price_i18n": "services.span_text.from_199.94483485",
                "img": "catalog-ai-video-generator",
                "alt": "Photos transforming into AI generated wedding film",
            },
            {
                "href": "/services/personalization/wedding-trailer/",
                "title": "Cinematic Wedding Trailer",
                "title_i18n": "order.option_text.cinematic_wedding_trailer.96782339",
                "desc": "Hollywood-style 1–3 minute trailer with licensed music.",
                "desc_i18n": "services.p_text.hollywood_style_1_3_minute_trailer_with.72173438",
                "price": "From $399",
                "price_i18n": "services.span_text.from_399.31596268",
                "img": "catalog-wedding-trailer",
                "alt": "Hollywood premiere style wedding trailer moment",
            },
            {
                "href": "/services/personalization/pet-wedding/",
                "title": "Pet Wedding Video",
                "title_i18n": "blog.skip-wedding-videographer.a_text.pet_wedding_video.27877847",
                "desc": "Include your furry family members in the celebration.",
                "desc_i18n": "services.p_text.include_your_furry_family_members_in_the.41918593",
                "price": "From $149",
                "price_i18n": "services.span_text.from_149.82399004",
                "img": "catalog-pet-wedding",
                "alt": "Pet in wedding tuxedo with flower crown",
            },
            {
                "href": "/services/personalization/multilingual/",
                "title": "Multilingual Wedding Video",
                "title_i18n": "order.option_text.multilingual_wedding_video.43523203",
                "desc": "20+ language support for international family and friends.",
                "desc_i18n": "services.p_text.20_language_support_for_international_fa.26489587",
                "price": "From $99",
                "price_i18n": "services.span_text.from_99.96638139",
                "img": "catalog-multilingual",
                "alt": "Wedding video with multiple language subtitles",
            },
            {
                "href": "/services/personalization/cartoon-style/",
                "title": "Cartoon / Animated Style",
                "title_i18n": "order.option_text.cartoon_animated_style.39055971",
                "desc": "Ghibli, Pixar, anime, watercolor — your wedding, animated.",
                "desc_i18n": "services.p_text.ghibli_pixar_anime_watercolor_your_weddi.64141418",
                "price": "From $149",
                "price_i18n": "services.span_text.from_149.82399004",
                # 1:1 mirror of the gallery case-study video (case-liu-wang-ghibli-…).
                # Replaces the static catalog-cartoon-style.jpg so visitors see the
                # actual rendered cartoon-style output instead of a generic still.
                # Version ?v=4.29 matches gallery/index.html (cache-bust parity).
                "video": {
                    "width": 1376,
                    "height": 768,
                    "poster": "/images/case-liu-wang-ghibli-wedding-film-poster.webp",
                    "webm": "/images/case-liu-wang-ghibli-wedding-film.webm?v=4.29",
                    "mp4": "/images/case-liu-wang-ghibli-wedding-film.mp4?v=4.29",
                    "aria_label": "Liu & Wang — Studio Ghibli style watercolor animation of a Chinese couple under a cherry blossom tree with falling petals at sunset",
                },
            },
            {
                "href": "/services/personalization/meme-generator/",
                "title": "Wedding GIFs & Memes",
                "title_i18n": "order.option_text.wedding_gifs_memes.90196302",
                "desc": "Shareable clips for social media and group chats.",
                "desc_i18n": "services.p_text.shareable_clips_for_social_media_and_gro.03144847",
                "price": "From $79",
                "price_i18n": "services.span_text.from_79.00659996",
                # 1:1 mirror of the gallery case-study video (case-williams-
                # family-30-gifs-aunt-linda-…). Replaces the static
                # catalog-meme-generator.jpg so visitors see Aunt Linda's
                # actual reaction GIF in motion instead of a generic still.
                # Version ?v=4.29 matches gallery/index.html (cache-bust parity).
                # No `style` attr — same as cartoon-style, gallery pattern.
                "video": {
                    "width": 1376,
                    "height": 768,
                    "poster": "/images/case-williams-family-30-gifs-aunt-linda-poster.webp",
                    "webm": "/images/case-williams-family-30-gifs-aunt-linda.webm?v=4.29",
                    "mp4": "/images/case-williams-family-30-gifs-aunt-linda.mp4?v=4.29",
                    "aria_label": "The Williams Family — Aunt Linda's shocked cake-cutting face became the family's universal response GIF, reused 50+ times in the group chat",
                },
            },
        ],
    },
}


def hreflangs(slug: str) -> str:
    """Generate the 10 link rel=alternate hreflang tags + canonical + x-default."""
    out = [f'    <link rel="canonical" href="https://weddingai.video/services/{slug}/">']
    for code, _ in LANGS:
        out.append(f'    <link rel="alternate" hreflang="{code}" href="https://weddingai.video/{code}/services/{slug}/">')
    out.append('    <link rel="alternate" hreflang="x-default" href="https://weddingai.video/services/{0}/">'.format(slug))
    return "\n".join(out)


def nav_html() -> str:
    items = "\n".join(
        f'                            <li role="none"><a role="menuitem" href="{href}" data-i18n="{key}">{label}</a></li>'
        for href, key, label in NAV_ITEMS
    )
    return f"""        <nav class="main-nav" aria-label="Main navigation">
                <ul class="nav-list">
                    <li class="nav-item-dropdown">
                        <a href="/#services" title="Browse our wedding video services" data-i18n="404.a_text.services.84864121" aria-haspopup="true" aria-expanded="false">Services <span aria-hidden="true">▾</span></a>
                        <ul class="nav-dropdown" role="menu">
{items}
                        </ul>
                    </li>
                    <li><a href="/gallery/" title="View our gallery and case studies" data-i18n="404.a_text.gallery.96646935">Gallery</a></li>
                    <li><a href="/blog/" title="Read our wedding video blog" data-i18n="404.a_text.blog.95723762">Blog</a></li>
                    <li><a href="/resources/" title="In-depth wedding video guides" data-i18n="404.a_text.resources.rrrrrrr1">Resources</a></li>
                    <li><a href="/about/" title="Learn about us" data-i18n="404.a_text.about.69447212">About</a></li>
                    <li><a href="/pricing/" title="View transparent pricing" data-i18n="404.a_text.pricing.43854765">Pricing</a></li>
                    <li><a href="/order/" class="btn-nav" title="Get a free quote — start your project" data-i18n="404.a_text.get_a_quote.03314957">Get a Quote</a></li>
                    <li class="wa-lang-switcher" data-no-i18n><select id="wa-lang-select" aria-label="Language"><option value="en">EN</option><option value="zh">中文</option><option value="es">ES</option><option value="fr">FR</option><option value="de">DE</option><option value="pt">PT</option><option value="ja">JA</option><option value="ru">RU</option><option value="ar">AR</option><option value="th">TH</option></select></li>
                </ul>
            </nav>"""


def service_card(c: dict) -> str:
    """Render one service-sub-card. Default path: <picture> over the catalog image
    set. Optional `video` block swaps the picture for a 1:1 mirror of the gallery
    case-study video (same controls/autoplay/muted/loop/playsinline/preload="none"
    + data-lazy-video so js/lazy-videos.js defers the metadata fetch to window.load).
    Same `img`/`alt` keys are ignored when `video` is present — callers should drop
    them from the dict in that case to keep the data clean.
    """
    if "video" in c:
        v = c["video"]
        # Optional inline style — used by family-message for fluid 16:9 sizing in
        # narrow service-sub-card containers. Position matches the hand-edited
        # page (between height and poster) so the verifier's literal-string
        # comparison stays stable. Omit for entries that don't need it
        # (cartoon-style keeps gallery's exact no-style markup).
        style_attr = f' style="{v["style"]}"' if "style" in v else ""
        return f"""                    <div class="service-sub-card">
                        <video controls autoplay muted loop playsinline preload="none" width="{v['width']}" height="{v['height']}"{style_attr} poster="{v['poster']}" aria-label="{v['aria_label']}" data-lazy-video>
                            <source src="{v['webm']}" type="video/webm">
                            <source src="{v['mp4']}" type="video/mp4">
                        </video><h3><a href="{c['href']}" title="{c['title']}" data-i18n="{c['title_i18n']}">{c['title']}</a></h3>
                        <p  data-i18n="{c['desc_i18n']}">{c['desc']}</p>
                        <span class="price-hint"  data-i18n="{c['price_i18n']}">{c['price']}</span>
                    </div>"""
    img = c["img"]
    ext = c.get("ext", "jpg")  # most catalog images are .jpg; vintage uses .png
    return f"""                    <div class="service-sub-card">
                        <picture><source srcset="/images/{img}-360.webp 360w, /images/{img}-720.webp 720w, /images/{img}-1280.webp 1280w" type="image/webp" sizes="(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw"><img src="/images/{img}.{ext}" alt="{c['alt']}" loading="lazy" width="1376" height="768" srcset="/images/{img}-360.{ext} 360w, /images/{img}-720.{ext} 720w, /images/{img}-1280.{ext} 1280w" sizes="(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw">
                        </picture><h3><a href="{c['href']}" title="{c['title']}" data-i18n="{c['title_i18n']}">{c['title']}</a></h3>
                        <p  data-i18n="{c['desc_i18n']}">{c['desc']}</p>
                        <span class="price-hint"  data-i18n="{c['price_i18n']}">{c['price']}</span>
                    </div>"""


def render_page(group: dict) -> str:
    slug = group["slug"]
    name = group["name"]
    cards = "\n".join(service_card(c) for c in group["children"])
    return f"""<!DOCTYPE html>

<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title  data-i18n="services.{slug}.title_text.{name.lower().replace(' ', '_')}_services_weddingai_video.enhcat0001">{name} Services — WeddingAI.video</title>
{hreflangs(slug)}
    <meta property="og:image" content="https://weddingai.video/images/og-image-1200x630.webp">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="WeddingAI.video — {name} services">
    <meta property="og:image:type" content="image/webp">
    <meta name="description" data-i18n-attr="content:services.{slug}.meta_description.{group['intro'][:50].lower().replace(' ', '_').replace(',', '').replace('—', '')}.enhcat0001" content="{group['intro']}" />
    <meta name="keywords" content="wedding video {name.lower()}, {name.lower()} wedding video services, AI wedding {name.lower()}">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="theme-color" content="#D4AF37">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="WeddingAI.video">

    <link rel="stylesheet" href="/styles.min.css?v=3.26">
    <link rel="stylesheet" href="/styles/i18n.css">
<script defer src="/js/main.min.js?v=3.19"></script>
<script defer src="/js/lazy-videos.js?v=1.0"></script>
    <style>
        .page-hero-bg {{ background: linear-gradient(135deg, #E8D5B7 0%, #C9A96E 100%); }}
        .page-hero-overlay {{ background: rgba(44,44,44,0.6); }}
        .page-hero-content h1 {{ font-size: clamp(1.75rem,4vw,2.5rem); color: var(--color-white); margin-bottom: var(--spacing-sm); }}
        .page-hero-content p {{ font-size: 1.0625rem; color: rgba(255,255,255,0.85); max-width: 600px; }}
        .page-hero-small {{ min-height: 40vh; }}

        .breadcrumb {{ padding: var(--spacing-md) 0; font-size: 0.875rem; color: var(--color-text-light); }}
        .breadcrumb a {{ color: var(--color-primary); }}
        .breadcrumb span {{ margin: 0 var(--spacing-xs); }}

        .service-group {{ padding: var(--spacing-2xl) 0; }}
        .service-group-header {{ text-align: center; margin-bottom: var(--spacing-xl); }}
        .service-group-header h2 {{ font-size: clamp(1.5rem, 3vw, 2.25rem); color: var(--color-secondary); margin-bottom: var(--spacing-xs); }}
        .service-group-header p {{ color: var(--color-text-light); max-width: 600px; margin: 0 auto; }}
        .service-sub-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--spacing-md); }}
        .service-sub-card {{ background: var(--color-white); border-radius: var(--radius-lg); padding: var(--spacing-lg); border: 1px solid var(--color-border); transition: var(--transition); }}
        .service-sub-card:hover {{ border-color: var(--color-primary); transform: translateY(-2px); box-shadow: var(--shadow-md); }}
        .service-sub-card h3 {{ font-size: 1.125rem; color: var(--color-secondary); margin-bottom: var(--spacing-xs); }}
        .service-sub-card h3 a {{ color: var(--color-secondary); text-decoration: none; }}
        .service-sub-card h3 a:hover {{ color: var(--color-primary); }}
        .service-sub-card p {{ font-size: 0.9375rem; color: var(--color-text-light); margin-bottom: var(--spacing-sm); }}
        .price-hint {{ font-size: 0.875rem; font-weight: 700; color: var(--color-primary); }}
    </style>
    <!-- Google tag (gtag.js) — deferred to first interaction or idle (avoids wasted bytes on bouncers) -->
    <script nonce="__CSP_NONCE__">
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-4FE7KSJDNB', {{ send_page_view: false, transport_type: 'beacon' }});

    window.__loadGtag = function() {{
      if (window.__gtagLoaded) return;
      window.__gtagLoaded = true;
      var s = document.createElement('script');
      s.src = 'https://www.googletagmanager.com/gtag/js?id=G-4FE7KSJDNB';
      s.async = true;
      s.onload = function() {{
        gtag('event', 'page_view', {{
          page_title: document.title,
          page_location: location.href,
          page_path: location.pathname + location.search
        }});
      }};
      s.setAttribute('data-gtag-lazy', '1');
      document.head.appendChild(s);
    }};

    // Engaged users: load on first interaction.
    ['scroll','click','touchstart','keydown'].forEach(function(evt){{
      window.addEventListener(evt, window.__loadGtag, {{ once: true, passive: true, capture: true }});
    }});
    // Passive readers / non-interactors: fallback to idle / load+3s.
    window.addEventListener('load', function() {{
      if ('requestIdleCallback' in window) {{
        requestIdleCallback(window.__loadGtag, {{ timeout: 4000 }});
      }} else {{
        setTimeout(window.__loadGtag, 3000);
      }}
    }});
    </script>
    <!-- Google AdSense (lazy-loaded to avoid forced reflow during initial paint) -->
    <script>
    window.addEventListener('load', function() {{
      var loadAds = function() {{
        var s = document.createElement('script');
        s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1670381960525419';
        s.async = true;
        s.crossOrigin = 'anonymous';
        s.setAttribute('data-ad-sbygoogle-lazy', '1');
        document.head.appendChild(s);
      }};
      if ('requestIdleCallback' in window) {{
        requestIdleCallback(loadAds, {{ timeout: 4000 }});
      }} else {{
        setTimeout(loadAds, 3000);
      }}
    }});
    </script>
    <meta property="og:title" content="{name} Services — WeddingAI.video">
    <meta property="og:description" content="{group['intro']}">
    <meta property="og:url" content="https://weddingai.video/services/{slug}/">
    <meta name="twitter:card" content="summary_large_image">
    <meta property="og:site_name" content="WeddingAI.video">
    <meta property="og:locale" content="en_US">
    <meta property="og:type" content="website">
    <meta name="twitter:title" content="{name} Services — WeddingAI.video">
    <meta name="twitter:description" content="{group['intro']}">
    <meta name="twitter:image" content="https://weddingai.video/images/og-image-1200x630.webp">
<script src="/js/langs.js" defer></script>
<script src="/js/i18n.js?v=3.40" defer></script>
<script>
if ('serviceWorker' in navigator) {{
  window.addEventListener('load', function() {{
    navigator.serviceWorker.register('/sw.js', {{ scope: '/' }}).catch(function(err) {{
      console.warn('[SW] registration failed', err);
    }});
  }});
}}
</script>
</head>
<body>

    <a href="#main-content" class="skip-link" data-i18n="404.a_text.skip_to_main_content.85143743">Skip to main content</a>

                <header class="site-header">
        <div class="container header-inner">
            <a href="/" class="logo" title="WeddingAI.video — wedding video services"><picture><source srcset="/images/logo-full-178.avif 178w, /images/logo-full-356.avif 356w, /images/logo-full-712.avif 712w" type="image/avif" sizes="(max-width: 600px) 178px, 356px"><source srcset="/images/logo-full-178.webp 178w, /images/logo-full-356.webp 356w, /images/logo-full-712.webp 712w" type="image/webp" sizes="(max-width: 600px) 178px, 356px"><img src="/images/logo-full.jpeg" alt="WeddingAI.video" height="72" width="1619" fetchpriority="high" loading="eager" sizes="(max-width: 600px) 178px, 356px"></picture></a>
{nav_html()}
            <button class="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false"><span></span><span></span><span></span></button>
        </div>
    </header>

    <main id="main-content">
        <section class="page-hero page-hero-small">
            <div class="page-hero-bg"></div>
            <div class="page-hero-overlay"></div>
            <div class="container page-hero-content">
                <nav class="breadcrumb">
                    <a href="/" title="Home" data-i18n="services.absence-compensation.celebrity-message.a_text.home.90820803">Home</a><span><span>›</span>
                    <a href="/services/" title="Services" data-i18n="404.a_text.services.84864121">Services</a><span><span>›</span>
                    {name}
                </nav>
                <h1  data-i18n="{group['h1_i18n']}">{group['h1']}</h1>
                <p  data-i18n="{group['intro_i18n']}">{group['intro']}</p>
            </div>
        </section>

        <section class="service-group" style="background: var(--color-white);">
            <div class="container">
                <header class="service-group-header">
                    <h2  data-i18n="{group['i18n_name_key']}">{name}</h2>
                    <p  data-i18n="{group['intro_i18n']}">{group['intro']}</p>
                </header>
                <div class="service-sub-list">
{cards}
                </div>
            </div>
        </section>

        <section class="section section-dark">
            <div class="container">
                <div style="text-align:center; max-width:600px; margin:0 auto;">
                    <h2  data-i18n="services.h2_text.not_sure_what_you_need.72262208">Not Sure What You Need?</h2>
                    <p style="margin: var(--spacing-sm) 0 var(--spacing-lg);"  data-i18n="services.p_text.tell_us_about_your_day_and_we_ll_recomme.99017356">Tell us about your footage and we'll recommend the right enhancement.</p>
                    <a href="/order/" class="btn btn-primary btn-large" title="Get a free quote — start your project"  data-i18n="about.a_text.get_a_free_quote.53673839">Get a Free Quote →</a>
                </div>
            </div>
        </section>
    </main>

    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://weddingai.video/"}},
            {{"@type": "ListItem", "position": 2, "name": "Services", "item": "https://weddingai.video/services/"}},
            {{"@type": "ListItem", "position": 3, "name": "{name}", "item": "https://weddingai.video/services/{slug}/"}}
        ]
    }}
    </script>

    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "{name} Services",
        "description": "{group['intro']}",
        "url": "https://weddingai.video/services/{slug}/",
        "isPartOf": {{"@id": "https://weddingai.video/#website"}},
        "publisher": {{"@id": "https://weddingai.video/#organization"}}
    }}
    </script>

    <footer class="site-footer">
        <div class="container footer-inner">
            <div class="footer-brand">
                <a href="/" class="logo" title="WeddingAI.video — wedding video services"><picture><source srcset="/images/logo-full-178.avif 178w, /images/logo-full-356.avif 356w, /images/logo-full-712.avif 712w" type="image/avif" sizes="(max-width: 600px) 178px, 356px"><source srcset="/images/logo-full-178.webp 178w, /images/logo-full-356.webp 356w, /images/logo-full-712.webp 712w" type="image/webp" sizes="(max-width: 600px) 178px, 356px"><img src="/images/logo-full.jpeg" alt="WeddingAI.video" height="72" width="1619" loading="lazy" sizes="(max-width: 600px) 178px, 356px"></picture></a>
                <p  data-i18n="404.p_text.ai_powered_wedding_video_services_for_co.90691298">AI-powered wedding video services for couples worldwide.</p>
            </div>
            <nav class="footer-nav" aria-label="Footer navigation">                    <div class="footer-col">
                        <h3  data-i18n="404.a_text.services.84864121">Services</h3>
                        <ul>
                                                                                    <li><a href="/services/video-enhancement/slow-motion/" title="AI Slow Motion Enhancement" data-i18n="404.a_text.slow_motion.30129340">Slow Motion</a></li>
                            <li><a href="/services/absence-compensation/family-tribute/" title="Tribute to Loved Ones" data-i18n="404.a_text.family_tribute.39408322">Family Tribute</a></li>
                            <li><a href="/services/absence-compensation/family-message/" title="Remote Family Video Message" data-i18n="404.a_text.family_message.27013166">Family Message</a></li>
                            <li><a href="/services/personalization/ai-video-generator/" title="AI Wedding Video Generator" data-i18n="404.a_text.ai_video_generator.39420322">AI Video Generator</a></li>
                            <li><a href="/services/personalization/wedding-trailer/" title="Cinematic Wedding Trailer" data-i18n="404.a_text.wedding_trailer.04692297">Wedding Trailer</a></li>
                            <li><a href="/services/personalization/pet-wedding/" title="Pet Wedding Video" data-i18n="404.a_text.pet_wedding.23911820">Pet Wedding</a></li>
                            <li><a href="/services/personalization/multilingual/" title="Multilingual Wedding Video" data-i18n="404.a_text.multilingual.74639147">Multilingual</a></li>
                            <li><a href="/services/personalization/cartoon-style/" title="Cartoon / Animated Style" data-i18n="404.a_text.cartoon_style.16664616">Cartoon Style</a></li>
                            <li><a href="/services/personalization/meme-generator/" title="Wedding GIFs & Memes" title="Wedding GIFs &amp; Memes" data-i18n="404.a_text.wedding_memes.22951185">Wedding Memes</a></li>
                                                    </ul>
                    </div>
                    <div class="footer-col">
                        <h3  data-i18n="404.h3_text.company.16024258">Company</h3>
                        <ul>
                            <li><a href="/about/" title="Learn about us" data-i18n="404.a_text.about_us.90074652">About Us</a></li>
                            <li><a href="/gallery/" title="View our gallery and case studies" data-i18n="404.a_text.gallery.96646935">Gallery</a></li>
                            <li><a href="/order/" title="Get a free quote — start your project" data-i18n="404.a_text.get_a_quote.03314957">Get a Quote</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h3  data-i18n="404.h3_text.contact.47569808">Contact</h3>
                        <ul>
                            <li><a href="mailto:order@weddingai.video" title="Send us an email at order@weddingai.video">order@weddingai.video</a></li>
                        </ul>
                    </div></nav>
        </div>


        <div class="footer-bottom">
            <div class="container">
                <p  data-i18n="404.p_text.2026_weddingai_video_all_rights_reserve.73926096">© 2026 WeddingAI.video. All rights reserved.</p>
                <a href="/privacy/" title="Read our privacy policy" data-i18n="404.a_text.privacy_policy.78442268">Privacy Policy</a> · <a href="/terms/" title="Read our terms of service" data-i18n="404.a_text.terms_of_service.30659181">Terms of Service</a>
            </div>
        </div>
    </footer>

    <!-- Schema.org Structured Data -->
    <script type="application/ld+json">{{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "WeddingAI.video",
        "alternateName": "WeddingAI",
        "url": "https://weddingai.video",
        "logo": "https://weddingai.video/images/logo-full.jpeg",
        "description": "AI-powered wedding video services for couples worldwide.",
        "email": "order@weddingai.video",
        "foundingDate": "2024"
    }}</script>

</body>
</html>
"""


def main() -> int:
    for slug, group in GROUPS.items():
        out = ROOT / "services" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(group), encoding="utf-8")
        print(f"Wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
