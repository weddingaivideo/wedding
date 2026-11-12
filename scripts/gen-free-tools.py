#!/usr/bin/env python3
"""Generate the free planning-tool pages (US-SERP-informed content).

US SERP evidence used for page content (captured 2026-11-10/11 from live
US search results; Google's HTML SERP itself is rate-limited, so the ranked
result pages were read in full and their H1 / section order / data tables /
FAQ questions were used as the content model):

  checklist     theknot.com/content/12-month-wedding-planning-countdown,
                zola.com/expert-advice/your-ultimate-wedding-planning-checklist
                (12+ months -> day-of -> after; avg engagement 15 months)
  alcohol       wedbuild.com/wedding-alcohol-calculator, calculator.city
                (1 drink/guest/hour; 100 guests x 5h = 500 drinks)
  vows          pix.wedding/how-to-write-wedding-vows, rosevow.com,
                myweddingkit.co  (The Knot 2026: 61% write own vows;
                150-250 words; 4-part frame; Zola 2026: 63% reject AI vows)
  speech        thebestmanspeech.com, weddingshub.co.uk,
                theperfectwedding.com (best man speaks last; 3-5 min)
  guest-count   weddingnotepad.com/calculator/guest-count, myseatplan.com,
                simplifycalc.com (80-85% local, 50-70% destination)
  timeline      bespoke-bride.com, weddingtimeline.org, digitalrsvps.com
                (ceremony time is the anchor; vendor-ready PDF/.ics)
  gift          toolaspect.com, weddingcardboxes.net, moneydeck.io
                (The Knot: $150 avg; cover-your-plate is obsolete)
  name-change   usa.gov/name-change, namechange.com, travel.state.gov,
                legalhelp.us (SSA first, then DMV, then passport)
  thank-you     zola.com/wedding-planning/instant-thank-yous,
                text-my-wedding.com, easyregistry.com.au (4-6 weeks;
                never name the cash amount; batch mode)
  cake          plana.wedding/tools/cake-size-calculator,
                weddingcakeshub.com, wedcalc.co.uk (1x2in slice;
                UK finger vs US dessert portions; square +25-35%)
  dress-code    vogue.com/article/brides-share-wedding-dress-codes,
                weddingnotepad.com, rosevow.com (no white; black OK now)
  tipping       pix.wedding/wedding-tip-calculator, the-weddingplanner.com,
                tipcalculatorpro.com (service charge != gratuity; Zola 2026
                survey of 720 couples)
  countdown     countz.io, counterdown.com, watchisup.com (share link,
                iframe embed, IG story card, milestone screenshots)
  vendor-q      planinlove.com, edelryan.com, preciousmomentseventsllc.com
                (5 questions per category + red flags)

Every generated page carries: full 11+x-default hreflang graph, WebApplication
and FAQPage JSON-LD with FAQ count matching the visible <details> blocks,
no inline event handlers (CSP is nonce-only), and no data-i18n keys.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "wedding-budget-calculator" / "index.html"
ORIGIN = "https://weddingai.video"
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

src = SOURCE.read_text(encoding="utf-8")


def extract(tag_open_re: str, end_tag: str) -> str:
    m = re.search(tag_open_re, src, re.S)
    if not m:
        raise RuntimeError("missing " + tag_open_re)
    start = m.start()
    end = src.index(end_tag, start) + len(end_tag)
    return src[start:end]


HEADER = extract(r'<header class="site-header">', "</header>")
FOOTER = extract(r'<footer class="site-footer">', "</footer>")
MAIN_OPEN = re.search(r"<main[^>]*>", src).group(0)

SIBLING_LINKS = [
    ("Budget Calculator", "/tools/wedding-budget-calculator/"),
    ("Seating Chart", "/tools/wedding-seating-chart-maker/"),
    ("Hashtag Generator", "/tools/wedding-hashtag-generator/"),
    ("Invitation Maker", "/tools/wedding-invitation-maker/"),
    ("Save the Date", "/tools/save-the-date-maker/"),
    ("Photo Book Planner", "/tools/wedding-photo-book-planner/"),
    ("Photo Collage", "/tools/wedding-photo-collage/"),
    ("HEIC to JPG", "/tools/heic-to-jpg-wedding-photos/"),
]


def hreflang(slug: str) -> str:
    base = f"/tools/{slug}/"
    lines = [f'<link rel="alternate" hreflang="en" href="{ORIGIN}{base}">']
    for lang in LANGS:
        lines.append(f'<link rel="alternate" hreflang="{lang}" href="{ORIGIN}/{lang}{base}">')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{ORIGIN}{base}">')
    return "\n".join(lines)


def faq_schema(faq: list[tuple[str, str]]) -> str:
    entities = [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in faq
    ]
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities},
                      ensure_ascii=False, indent=2)


def app_schema(t: dict) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": t["name"],
        "url": f"{ORIGIN}/tools/{t['slug']}/",
        "applicationCategory": t.get("category", "UtilitiesApplication"),
        "operatingSystem": "Any (browser-based)",
        "browserRequirements": "Requires JavaScript",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": t["description"],
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "WeddingAI.video", "url": ORIGIN + "/"},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def faq_html(faq: list[tuple[str, str]]) -> str:
    # `qa-block` is the markup form the site's schema-consistency gate counts
    # as visible FAQs (see scripts/verify-schemas.py). `ft-faq` carries styling.
    out = ['            <h2>Frequently asked questions</h2>', '            <div class="qa-block ft-faq">']
    for q, a in faq:
        out.append("                <details>")
        out.append(f"                    <summary>{q}</summary>")
        out.append(f"                    <p>{a}</p>")
        out.append("                </details>")
    out.append("            </div>")
    return "\n".join(out)


def siblings_html(slug: str) -> str:
    links = [(label, href) for label, href in SIBLING_LINKS if slug not in href]
    links += [(t["short"], f"/tools/{t['slug']}/") for t in TOOLS if t["slug"] != slug][:5]
    seen, out = set(), ['            <h2>More free wedding tools</h2>',
                        '            <div class="ft-siblings" aria-label="More free wedding tools">']
    for label, href in links:
        if href in seen:
            continue
        seen.add(href)
        out.append(f'                <a href="{href}">{label}</a>')
    out.append("            </div>")
    return "\n".join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>__TITLE__</title>
    <link rel="canonical" href="__CANON__">
    <meta name="description" content="__DESC__">
    <meta name="keywords" content="__KEYWORDS__">
    <meta property="og:type" content="website">
    <meta property="og:title" content="__OGTITLE__">
    <meta property="og:description" content="__DESC__">
    <meta property="og:url" content="__CANON__">
    <meta property="og:site_name" content="WeddingAI.video">
    <meta property="og:locale" content="en_US">
    <meta property="og:image" content="https://weddingai.video/images/og-image-1200x630.jpg">
    <meta property="og:image:alt" content="__NAME__">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="__OGTITLE__">
    <meta name="twitter:description" content="__DESC__">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="theme-color" content="#D4AF37">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="__NAME__">
__HREFLANG__
    <link rel="stylesheet" href="/styles.min.css?v=3.41">
    <link rel="stylesheet" href="/styles/tools.css?v=1.0.3">
    <link rel="stylesheet" href="/styles/free-tools.css?v=1.0.0">
    <script defer src="/js/main.min.js?v=3.22"></script>
    <script defer src="/js/tools/common.js?v=1.0.8"></script>
    <script defer src="/js/i18n.js?v=4.29"></script>
    <script defer src="/js/tools/free-tools.js?v=1.0.0"></script>
    <script type="application/ld+json">
__APPSCHEMA__
    </script>
    <script type="application/ld+json">
__FAQSCHEMA__
    </script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function (err) {
      console.warn('[SW] registration failed', err);
    });
  });
}
</script>
</head>
<body class="page-tool">
<a class="wa-skip-link" href="#main-content">Skip to main content</a>
__HEADER__
__MAIN_OPEN__
    <section class="page-hero-mini" style="background: linear-gradient(135deg, #2c2c2c 0%, #4a4a4a 50%, #d4af37 100%); color: #fff; text-align: center; padding: var(--spacing-xl) var(--spacing-md);">
        <h1 style="color: #fff; font-size: clamp(1.75rem, 4vw, 2.5rem); margin-bottom: .5rem;">__H1__</h1>
        <p style="color: rgba(255,255,255,.85); max-width: 720px; margin: 0 auto;">__LEDE__</p>
    </section>
    <nav class="breadcrumb" aria-label="Breadcrumb" style="max-width: 1140px; margin: 0 auto; padding: var(--spacing-md); font-size: .875rem; color: var(--color-text-light);">
        <a href="/">Home</a><span> / </span><a href="/tools/">Free Tools</a><span> / </span>__NAME__
    </nav>
    <section class="ft-shell" aria-label="__NAME__ tool">
        <div class="ft-grid">
            <div class="ft-panel">
                <div class="ft-card">
                    <h2>__PANEL_TITLE__</h2>
__PANEL__
                </div>
                <div class="ft-privacy">Runs entirely in your browser. Nothing you type is uploaded, saved to a server, or shared. Your inputs stay in this device's local storage.</div>
            </div>
            <div class="ft-results">
                <h2>__RESULT_TITLE__</h2>
                <div class="ft-stats" id="ft-stats"></div>
                <div class="ft-table-wrap" id="ft-table"></div>
                <div id="ft-output"></div>
                <div id="ft-groups"></div>
                <div class="ft-callout" id="ft-note" style="display:none;"></div>
                <div id="ft-progress-wrap" style="display:none;">
                    <div class="ft-progress"><div class="ft-progress-fill" id="ft-progress-fill"></div></div>
                    <p class="ft-hint" id="ft-progress-label">0 of 0 done</p>
                </div>
                <div class="ft-actions">
                    <button type="button" class="ft-btn ft-btn-primary" id="ft-copy">Copy result</button>
                    <button type="button" class="ft-btn" id="ft-download">Download .txt</button>
                    <button type="button" class="ft-btn" id="ft-print">Print / PDF</button>
                    <button type="button" class="ft-btn" id="ft-again" style="display:none;">Another version</button>
                    <button type="button" class="ft-btn" id="ft-reset">Reset</button>
                </div>
            </div>
        </div>
    </section>
    <section class="ft-article">
__ARTICLE__
__FAQHTML__
__SIBLINGS__
    </section>
    <section class="cta-section" style="background: var(--color-secondary); color: #fff; text-align: center; padding: var(--spacing-xl) 0;">
        <div class="container">
            <h2 style="color: #fff;">__CTA_TITLE__</h2>
            <p style="color: rgba(255,255,255,.78); margin-bottom: var(--spacing-md);">__CTA_TEXT__</p>
            <a href="/order/" class="btn btn-primary btn-large">Get a Free Quote &rarr;</a>
        </div>
    </section>
</main>
__FOOTER__
<script>
__CONFIG__
__LOGIC__
</script>
</body>
</html>
"""


def normalize_checkboxes(html: str) -> str:
    """Wrap the TEXT of a checkbox label in its own <span>.

    WHY
    ---
    A checkbox line looks like this:

        <label class="ft-checkline"><input type="checkbox" data-ft="toast"
        checked> Include one glass of bubbles each for the toast</label>

    The i18n binder walks the tree and skips the elements it must not
    translate - <input> is one of them. So a <label> whose only child is
    an <input> looks like a text-only element, and the binder puts a
    single data-i18n key on the LABEL. The dictionary value is then the
    label's whole inner markup, "<input type=...> Include one glass of
    bubbles each for the toast".

    The middleware replaces the inner HTML of a bound element with the
    dictionary value, so in every one of the ten languages that label
    would have been rewritten into a text line with a stray "<input
    type=...>" printed in front of it - and the checkbox itself would be
    gone, so the option could no longer be turned on.

    Putting the text in a <span> gives the binder a text-only element to
    bind. The <input> stays a sibling of the span and survives; the span's
    text is what gets translated.

    The label keeps its "for"/wrapping relationship, so clicking the text
    still toggles the checkbox.
    """
    pattern = re.compile(
        r'(<label\b[^>]*>\s*<input\b[^>]*>)(\s*)([^<]+?)(</label>)')
    return pattern.sub(lambda m: "%s%s<span>%s</span>%s" % (m.group(1), m.group(2), m.group(3), m.group(4)), html)


def render(t: dict) -> str:
    canon = f"{ORIGIN}/tools/{t['slug']}/"
    html = TEMPLATE
    for key, value in {
        "__TITLE__": t["title"], "__CANON__": canon, "__DESC__": t["description"],
        "__KEYWORDS__": t.get("keywords", ""), "__OGTITLE__": t.get("og_title", t["name"]),
        "__NAME__": t["name"], "__HREFLANG__": hreflang(t["slug"]),
        "__APPSCHEMA__": app_schema(t), "__FAQSCHEMA__": faq_schema(t["faq"]),
        "__HEADER__": HEADER, "__FOOTER__": FOOTER, "__MAIN_OPEN__": MAIN_OPEN,
        "__H1__": t["h1"], "__LEDE__": t["lede"],
        "__PANEL_TITLE__": t.get("panel_title", "Your details"),
        "__PANEL__": t["panel"], "__RESULT_TITLE__": t.get("result_title", "Your result"),
        "__ARTICLE__": t["article"], "__FAQHTML__": faq_html(t["faq"]),
        "__SIBLINGS__": siblings_html(t["slug"]),
        "__CTA_TITLE__": t.get("cta_title", "Planning done? Let's make the film."),
        "__CTA_TEXT__": t.get("cta_text", "Turn the photos and words from your planning into a 60–90 second cinematic wedding film."),
        "__CONFIG__": "window.FT_CONFIG = " + json.dumps({
            "mode": t["mode"], "storageKey": "ft-" + t["slug"],
            "downloadName": t["slug"],
        }, indent=2) + ";",
        "__LOGIC__": t["logic"].strip(),
    }.items():
        html = html.replace(key, value)
    html = normalize_checkboxes(html)
    return html


TOOLS: list[dict] = []

# ---------------------------------------------------------------------------
# Tool definitions. Content mirrors the ranked US result pages above.
# ---------------------------------------------------------------------------

TOOLS.append({
    "slug": "wedding-checklist-generator",
    "name": "Wedding Planning Checklist Generator",
    "short": "Planning Checklist",
    "title": "Wedding Planning Checklist Generator: Month-by-Month, Free",
    "description": "Free wedding planning checklist built around your date. 12+ months to day-of, 100+ tasks, progress saved in your browser. No signup, printable.",
    "keywords": "wedding planning checklist, wedding checklist generator, wedding timeline checklist, 12 month wedding checklist, printable wedding checklist",
    "og_title": "Free Wedding Planning Checklist — Built Around Your Date",
    "category": "ProductivityApplication",
    "h1": "Wedding Planning Checklist Generator",
    "lede": "A month-by-month plan built around your wedding date, from 12+ months out to the day after. Tick tasks off in your browser — nothing is uploaded.",
    "panel_title": "Set your date",
    "result_title": "Your planning timeline",
    "mode": "checklist",
    "panel": """                    <div class="ft-row">
                        <label class="ft-label" for="ft-date">Wedding date</label>
                        <input class="ft-input" type="date" id="ft-date" data-ft="date" data-ft-default="">
                    </div>
                    <div class="ft-row">
                        <label class="ft-label" for="ft-scope">Wedding style</label>
                        <select class="ft-select" id="ft-scope" data-ft="scope">
                            <option value="full">Traditional / full wedding</option>
                            <option value="small">Small wedding (under 50 guests)</option>
                            <option value="destination">Destination wedding</option>
                            <option value="elopement">Elopement / micro wedding</option>
                        </select>
                    </div>
                    <p class="ft-hint">The Knot's 2026 Real Weddings Study puts the average US engagement at 15 months. This checklist covers 12+ months but adapts to however long you have.</p>
                    <div class="ft-actions">
                        <button type="button" class="ft-btn" id="ft-print">Print checklist</button>
                    </div>""",
    "article": """
        <h2>What a US wedding checklist actually covers</h2>
        <p>The two pages that dominate US search for this task — The Knot's 12-month planning countdown and Zola's ultimate checklist — use the same spine: <strong>12+ months out, then one section per month, then 2 weeks / week before / day before / day of / after the wedding</strong>. Both note that the average engagement is about 15 months, so the first block is research and vision, not bookings.</p>
        <p>Our generator follows that structure and adds the one thing a printed PDF cannot: a live progress bar and a saved state in your browser. Tick a task today, come back in three weeks, and it is still ticked. Copy or print the whole list when a planner or parent asks for it.</p>
        <h2>The milestones that drive every other decision</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>When</th><th>What must be decided</th><th>Why it comes first</th></tr></thead>
            <tbody>
                <tr><td>12+ months</td><td>Budget, guest list draft, overall vision, engagement party</td><td>Guest count drives venue size, catering and invitation quantities</td></tr>
                <tr><td>12–9 months</td><td>Venue, date, planner, photographer, videographer</td><td>Peak-season venues and photographers book 12+ months ahead</td></tr>
                <tr><td>8–6 months</td><td>Catering, bar, attire, save-the-dates, hotel blocks</td><td>Destination guests need 8–12 months' notice per US RSVP guidance</td></tr>
                <tr><td>3 months</td><td>Invitations, hair &amp; makeup trial, thank-you gifts</td><td>Formal invitations go out 2–3 months before (4–6 for destination)</td></tr>
                <tr><td>2 months</td><td>Vows, alterations, favors, final fittings</td><td>Both The Knot and Zola flag vows here — not the night before</td></tr>
                <tr><td>1 month → day of</td><td>Final headcount, seating chart, vendor timeline, marriage license</td><td>Caterers need a firm number 7–14 days out</td></tr>
                <tr><td>After</td><td>Thank-you cards, name change, photo album, reviews</td><td>US etiquette targets 4–6 weeks for thank-you notes</td></tr>
            </tbody>
        </table></div>
        <h2>Where the words come in</h2>
        <p>Two checklist items are consistently the hardest: <a href="/tools/wedding-vow-writer/">writing personal vows</a> and <a href="/tools/wedding-speech-writer/">drafting the reception speeches</a>. According to The Knot's 2026 Real Weddings Study of 10,474 couples, 61% of couples now write their own vows — the highest rate recorded — so "start your vows" has moved from a nice-to-have to a standard two-month-out task. Both have their own free tool here.</p>
        <h2>From the checklist to the film</h2>
        <p>Nearly every item on this list produces something temporary: a menu, a seating plan, a timeline. The two things you keep are the photographs and the film. Once your date and venue are locked, <a href="/blog/wedding-video-from-photos/">see how a cinematic wedding film is built from photos</a> or <a href="/tools/wedding-budget-calculator/">model the video line in your budget</a>.</p>
    """,
    "faq": [
        ("How long before the wedding should I start planning?", "The Knot's 2026 Real Weddings Study reports an average engagement of 15 months in the US. Twelve months is a comfortable planning window; a small wedding or elopement can be organised in 3–6 months. The checklist adapts to whatever date you enter, keeping the order of tasks intact."),
        ("When should wedding invitations be mailed?", "US etiquette guidance puts formal invitations at 2–3 months before the wedding, and 4–6 months ahead for a destination wedding. Save-the-dates go out 6–8 months ahead locally and 10–12 months ahead for destination weddings."),
        ("Is my checklist saved anywhere?", "Only in this browser's local storage on this device. Nothing is sent to a server and there is no account. Clearing browser storage removes the saved ticks — use Print or Copy result first if you want a permanent copy."),
        ("Can I print the checklist or share it with my planner?", "Yes. Print / PDF produces a clean list without the tool controls, and Copy result gives you plain text you can paste into an email, a shared document, or a planning spreadsheet."),
        ("Does this work for a small wedding or elopement?", "Yes. Choose Small wedding, Destination, or Elopement and the checklist is filtered to the tasks that still apply — you will not be chased about hotel blocks or a 200-person seating plan."),
        ("When should we write our vows?", "Both The Knot and Zola place the first vow draft about two months out. Write a loose structure early, then refine it; 61% of US couples now write personal vows, and 150–250 words is the usual target length."),
    ],
    "cta_title": "Every box ticked? Keep the day.",
    "cta_text": "The timeline ends, the venue empties, and the film is what you watch again. Turn your photos into a 60–90 second cinematic wedding film.",
    "logic": r"""
window.FT_GROUPS = [
  { title: '12+ months out — vision and groundwork', items: [
    { id: 'a1', text: 'Celebrate, then agree on the big picture: season, region, rough size' },
    { id: 'a2', text: 'Set the total budget and who is contributing' },
    { id: 'a3', text: 'Draft a rough guest list (must-invite / hope-to / if space)' },
    { id: 'a4', text: 'Start a shared inspiration board and a wedding-only email address' },
    { id: 'a5', text: 'Decide on an engagement party and start a small registry' },
    { id: 'a6', text: 'Research venues and note their capacity, curfew and rain plan' }
  ]},
  { title: '12–9 months out — lock the big vendors', items: [
    { id: 'b1', text: 'Tour and book the ceremony and reception venue' },
    { id: 'b2', text: 'Set the date and time, and confirm the ceremony officiant' },
    { id: 'b3', text: 'Hire a planner or day-of coordinator if you want one' },
    { id: 'b4', text: 'Book photographer and videographer (peak dates go first)' },
    { id: 'b5', text: 'Book catering and bar, and confirm the alcohol policy' },
    { id: 'b6', text: 'Book entertainment (DJ or band) and ceremony musicians' },
    { id: 'b7', text: 'Start a wedding website with travel and accommodation details' }
  ]},
  { title: '8–6 months out — details and guest logistics', items: [
    { id: 'c1', text: 'Shop for attire and allow 4–6 weeks for alterations later' },
    { id: 'c2', text: 'Send save-the-dates (10–12 months ahead for destination)' },
    { id: 'c3', text: 'Reserve hotel blocks and check passport rules for guests' },
    { id: 'c4', text: 'Book florist, hair and makeup, transport and rentals' },
    { id: 'c5', text: 'Plan the menu tasting and confirm dietary requirements' },
    { id: 'c6', text: 'Choose the wedding party and ask them formally' }
  ]},
  { title: '5–3 months out — invitations and fittings', items: [
    { id: 'd1', text: 'Finalise the invitation design, wording and dress code line' },
    { id: 'd2', text: 'Mail formal invitations 2–3 months before (4–6 destination)' },
    { id: 'd3', text: 'Schedule the hair and makeup trial' },
    { id: 'd4', text: 'Buy thank-you gifts for the wedding party, officiant and parents' },
    { id: 'd5', text: 'Confirm the ceremony reading, music and procession order' },
    { id: 'd6', text: 'Order the cake and confirm delivery and setup' }
  ]},
  { title: '2 months out — the words', items: [
    { id: 'e1', text: 'Write a first draft of personal vows (150–250 words each)' },
    { id: 'e2', text: 'Ask the best man, maid of honour and parents to draft speeches' },
    { id: 'e3', text: 'Final attire fitting; confirm undergarments and shoes' },
    { id: 'e4', text: 'Order favors, welcome bags and signage' },
    { id: 'e5', text: 'Apply for the marriage license (check your state window)' },
    { id: 'e6', text: 'Build the photography shot list with your photographer' }
  ]},
  { title: '1 month out — confirmations', items: [
    { id: 'f1', text: 'Chase late RSVPs and finalise the headcount' },
    { id: 'f2', text: 'Build the seating chart and send it to the printer' },
    { id: 'f3', text: 'Send the final timeline to every vendor' },
    { id: 'f4', text: 'Confirm final payments, gratuities and envelopes' },
    { id: 'f5', text: 'Break in your shoes and pack a day-of emergency kit' },
    { id: 'f6', text: 'Give the caterer the firm meal count (7–14 days before)' }
  ]},
  { title: 'Final week and the day', items: [
    { id: 'g1', text: 'Rehearsal and rehearsal dinner' },
    { id: 'g2', text: 'Deliver decor, favors, signs and the guest book to the venue' },
    { id: 'g3', text: 'Hand the timeline and point of contact to the coordinator' },
    { id: 'g4', text: 'Charge devices, confirm transport and weather backup' },
    { id: 'g5', text: 'Eat breakfast, drink water, and hand over the rings' }
  ]},
  { title: 'After the wedding', items: [
    { id: 'h1', text: 'Send thank-you cards within 4–6 weeks' },
    { id: 'h2', text: 'Review every vendor and return any rentals' },
    { id: 'h3', text: 'Start the name-change sequence if applicable (SSA first)' },
    { id: 'h4', text: 'Back up the guest photos and order the album' },
    { id: 'h5', text: 'Save the top cake tier if that is your tradition' }
  ]}
];
window.FT_INIT = function (api) {
  var wrap = api.$('#ft-progress-wrap');
  if (wrap) wrap.style.display = '';
  var dateInput = api.$('[data-ft="date"]');
  if (dateInput) {
    dateInput.addEventListener('change', function () {
      if (!dateInput.value) return;
      var d = new Date(dateInput.value + 'T12:00:00');
      if (isNaN(d.getTime())) return;
      var months = Math.max(0, Math.round((d - new Date()) / 2629800000));
      var note = api.$('#ft-note');
      if (note) {
        note.style.display = '';
        note.textContent = 'About ' + months + ' months to go. Work through the blocks in order and skip any that do not apply to your wedding.';
      }
    });
  }
};
""",
})

TOOLS.append({
    "slug": "wedding-alcohol-calculator",
    "name": "Wedding Alcohol Calculator",
    "short": "Alcohol Calculator",
    "title": "Wedding Alcohol Calculator: How Much Beer, Wine & Liquor",
    "description": "Free wedding alcohol calculator. Enter guests and bar hours for a shopping list of wine, beer, spirits and toast bubbles. US standard pours. Browser-side, no signup.",
    "keywords": "wedding alcohol calculator, wedding drink calculator, how much alcohol for 100 guests, wedding bar calculator, liquor calculator for wedding",
    "og_title": "Free Wedding Alcohol Calculator — Exact Bottles & Cases",
    "category": "FinanceApplication",
    "h1": "Wedding Alcohol Calculator",
    "lede": "How much wine, beer and spirits do you actually need? The industry rule is one drink per guest per hour — this turns it into a shopping list in bottles and cases.",
    "panel_title": "Your reception",
    "result_title": "What to buy",
    "mode": "calc",
    "panel": """                    <div class="ft-row-2">
                        <div class="ft-row"><label class="ft-label" for="ft-guests">Guests who drink</label><input class="ft-input" type="number" min="1" max="2000" value="100" data-ft="guests" data-ft-default="100"></div>
                        <div class="ft-row"><label class="ft-label" for="ft-hours">Bar open (hours)</label><input class="ft-input" type="number" min="1" max="12" value="5" data-ft="hours" data-ft-default="5"></div>
                    </div>
                    <div class="ft-row"><label class="ft-label" for="ft-pace">Drinks per guest per hour</label>
                        <select class="ft-select" id="ft-pace" data-ft="pace"><option value="1">1 — standard (the general rule)</option><option value="1.2">1.2 — lively crowd</option><option value="1.5">1.5 — big night</option><option value="0.8">0.8 — daytime / light</option></select>
                    </div>
                    <div class="ft-row"><label class="ft-label" for="ft-mix">Drink mix</label>
                        <select class="ft-select" id="ft-mix" data-ft="mix"><option value="balanced">Balanced 50% wine / 30% beer / 20% spirits</option><option value="wine">Mostly wine 70 / 15 / 15</option><option value="beer">Mostly beer 25 / 60 / 15</option><option value="nospirits">Wine &amp; beer only 60 / 40 / 0</option></select>
                    </div>
                    <div class="ft-row"><label class="ft-label" for="ft-region">Bottle standard</label>
                        <select class="ft-select" id="ft-region" data-ft="region"><option value="us">US — 750ml wine, 12oz beer, 1.5oz shot</option><option value="au">AU — 750ml wine, 375ml cans, 700ml spirits</option></select>
                    </div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="toast" checked> Include one glass of bubbles each for the toast</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="buffer" checked> Add a 10% safety buffer</label>""",
    "article": """
        <h2>The rule behind every wedding bar calculator</h2>
        <p>Ranked US tools (WedBuild, Calculator City, and the catering guides they cite) all start from the same planning rule: <strong>one drink per drinking guest for every hour the bar is open</strong>, rising to two or three for a crowd that likes a big night. That number is then split across wine, beer and spirits and converted into purchase units. Our default — 100 drinking guests over five hours — gives 500 drinks, exactly the worked example used on the top-ranking page.</p>
        <p>Two details matter more than the arithmetic. First, count <strong>drinkers, not invitations</strong>: children, drivers and guests who do not drink are excluded, and destination or Sunday-afternoon weddings skew lower. Second, check what the venue already supplies before buying anything — many catering packages include the bar, and some venues forbid outside alcohol.</p>
        <h2>Standard pours used here (US)</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Drink</th><th>One serving</th><th>Servings per bottle / case</th></tr></thead>
            <tbody>
                <tr><td>Wine</td><td>5 oz (150 ml)</td><td>5 per 750 ml bottle</td></tr>
                <tr><td>Beer</td><td>12 oz can or bottle</td><td>24 per case</td></tr>
                <tr><td>Spirits</td><td>1.5 oz shot</td><td>16 per 750 ml bottle</td></tr>
                <tr><td>Sparkling (toast)</td><td>5 oz glass</td><td>5 per 750 ml bottle</td></tr>
            </tbody>
        </table></div>
        <p>The pour definitions match the US National Institute on Alcohol Abuse and Alcoholism's standard-drink guidance, which the leading calculators also cite. Switch to the AU standard if you are buying in Australia: 375 ml cans and 700 ml spirit bottles change the case math noticeably.</p>
        <h2>Worked example: 100 guests, five hours</h2>
        <p>At one drink per hour with a balanced 50/30/20 split, the shopping list lands near <strong>50 bottles of wine, 7 cases of beer and 5 bottles of spirits</strong>, plus about 20 bottles of sparkling wine if every guest gets a toast pour. Add 10% and you will not run short; unopened cases can usually be returned, so erring high costs little.</p>
        <h2>Planning the rest of the reception</h2>
        <p>Alcohol is only one line in the catering conversation. Pair this with the <a href="/tools/wedding-cake-serving-calculator/">cake serving calculator</a> for dessert portions, the <a href="/tools/wedding-guest-count-calculator/">guest count calculator</a> to firm up the headcount before RSVPs arrive, and the <a href="/tools/wedding-budget-calculator/">budget calculator</a> to see how the bar sits against the total. These are estimates for purchasing, not guidance about consumption — offer food, water and good non-alcoholic options, and make sure everyone has a safe way home.</p>
    """,
    "faq": [
        ("How much alcohol do I need for 100 wedding guests?", "At one drink per guest per hour over a five-hour reception, plan for 500 drinks. With a balanced 50% wine / 30% beer / 20% spirits split that is about 50 bottles of wine, 7 cases of beer and 5 bottles of spirits, plus roughly 20 bottles of sparkling wine if everyone gets a toast pour."),
        ("How many drinks per guest per hour should I plan for?", "One per hour is the standard planning rule. Use 0.8 for a daytime or light-drinking crowd, 1.2 for a lively evening, and 1.5 for a big party. The figure is a purchasing estimate, not a target for anyone's consumption."),
        ("Should I count every invited guest?", "No. Count the guests who will actually drink — exclude children, designated drivers and non-drinkers. US RSVP guidance also suggests 80–85% of local invitees attend, and fewer for destination weddings, so start from a realistic headcount."),
        ("What is a standard drink pour?", "In the US: 5 oz of wine, 12 oz of beer, or 1.5 oz of spirits. A 750 ml wine bottle yields about 5 glasses, a case holds 24 beers, and a 750 ml spirit bottle yields about 16 shots. The calculator uses these conversions and always rounds up."),
        ("Do I need sparkling wine for the toast?", "Only if you are serving a toast pour to every guest. One 5 oz glass each means one 750 ml bottle per five drinking guests. Many venues pour the toast from the regular wine order instead, so check the catering package first."),
        ("Can I bring my own alcohol to the venue?", "Sometimes. Many US venues allow self-supplied alcohol but charge a corkage fee, while others require their licensed bar package. Confirm the policy in writing before buying — this calculator works out the gap you need to cover."),
    ],
    "logic": r"""
window.FT_COMPUTE = function (v) {
  var guests = Math.max(1, v.guests || 1);
  var hours = Math.max(1, v.hours || 1);
  var pace = parseFloat(v.pace) || 1;
  var mixes = {
    balanced: [0.50, 0.30, 0.20], wine: [0.70, 0.15, 0.15],
    beer: [0.25, 0.60, 0.15], nospirits: [0.60, 0.40, 0]
  };
  var mix = mixes[v.mix] || mixes.balanced;
  var au = v.region === 'au';
  var winePer = 5, beerPer = 24, spiritPer = au ? 23 : 16;
  var total = guests * hours * pace;
  if (v.buffer) total *= 1.10;
  var wineDrinks = total * mix[0], beerDrinks = total * mix[1], spiritDrinks = total * mix[2];
  var wineBottles = Math.ceil(wineDrinks / winePer);
  var beerCases = Math.ceil(beerDrinks / beerPer);
  var spiritBottles = Math.ceil(spiritDrinks / spiritPer);
  var toastBottles = v.toast ? Math.ceil(guests / winePer) : 0;
  var rows = [
    ['Wine (750 ml)', wineBottles + ' bottles', Math.round(wineDrinks) + ' glasses'],
    ['Beer (' + (au ? '375 ml cans' : '12 oz') + ')', beerCases + ' cases', Math.round(beerDrinks) + ' servings'],
    ['Spirits (' + (au ? '700 ml' : '750 ml') + ')', spiritBottles + ' bottles', Math.round(spiritDrinks) + ' shots']
  ];
  if (v.toast) rows.push(['Sparkling for the toast', toastBottles + ' bottles', guests + ' glasses']);
  var lines = ['Wedding bar shopping list', guests + ' drinking guests x ' + hours + ' hours x ' + pace + ' drinks/hour', ''];
  rows.forEach(function (r) { lines.push(r[0] + ': ' + r[1] + ' (' + r[2] + ')'); });
  lines.push('', 'Count drinkers, not invitations. Ask the venue what its package already includes.');
  return {
    stats: [
      { num: Math.round(total), lbl: 'Total drinks', accent: true },
      { num: wineBottles, lbl: 'Wine bottles' },
      { num: beerCases, lbl: 'Beer cases' },
      { num: spiritBottles, lbl: 'Spirit bottles' }
    ],
    head: ['Buy', 'Quantity', 'Servings covered'], rows: rows,
    note: 'Rounded up to whole bottles and cases. These are purchasing estimates for a bar, not drinking guidance — offer water, food and non-alcoholic options, and arrange safe transport.',
    text: lines.join('\n')
  };
};
""",
})

TOOLS.append({
    "slug": "wedding-vow-writer",
    "name": "Wedding Vow Writer",
    "short": "Vow Writer",
    "title": "Wedding Vow Writer: Build Personal Vows in Four Parts (Free)",
    "description": "Free wedding vow builder using the four-part structure US couples use. 150-250 words, tone control, live word count and speaking time. No AI writes your words. Browser-side.",
    "keywords": "wedding vow writer, wedding vows examples, how to write wedding vows, personal wedding vows template, short wedding vows",
    "og_title": "Free Wedding Vow Writer — Your Words, Structured",
    "category": "WritingApplication",
    "h1": "Wedding Vow Writer",
    "lede": "61% of US couples now write their own vows. This builder gives you the four-part frame, a word budget and a speaking-time check — the words stay yours.",
    "panel_title": "Your vows",
    "result_title": "Your draft",
    "mode": "generator",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-name">Your partner's name</label><input class="ft-input" type="text" value="Alex" data-ft="name" data-ft-default="Alex" placeholder="First name"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-memory">One memory only you two share</label><textarea class="ft-textarea" data-ft="memory" placeholder="Where you were, what happened, what you noticed">The night we got lost driving home and ended up talking in the car until 2am.</textarea></div>
                    <div class="ft-row"><label class="ft-label" for="ft-quality">A specific thing you love</label><input class="ft-input" type="text" value="the way you remember every small detail" data-ft="quality" data-ft-default="the way you remember every small detail"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-promises">Three promises (one per line)</label><textarea class="ft-textarea" data-ft="promises">I will listen before I answer.
I will make coffee on the ordinary Tuesdays.
I will tell you the truth when it is hard.</textarea></div>
                    <div class="ft-row"><label class="ft-label" for="ft-tone">Tone</label><select class="ft-select" id="ft-tone" data-ft="tone"><option value="warm">Warm and conversational</option><option value="formal">Formal and traditional</option><option value="short">Short and understated</option><option value="playful">Playful with one light joke</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-length">Target length</label><select class="ft-select" id="ft-length" data-ft="length"><option value="150">Short — about 150 words</option><option value="200">Classic — about 200 words</option><option value="250">Full — about 250 words</option></select></div>
                    <p class="ft-hint">Zola's 2026 First Look Report found 63% of couples think AI has no place in writing vows. This tool never invents your stories — it only structures what you type.</p>""",
    "article": """
        <h2>Why vows are now the centre of the ceremony</h2>
        <p>The Knot's 2026 Real Weddings Study, based on 10,474 US couples married in 2025, found that <strong>61% wrote their own vows — the highest rate ever recorded</strong>, up from 44% in its 2019 study. As ceremonies move away from a fixed religious script, the vows carry more of the emotional weight. That also makes them harder to write: a vow has to sound like one specific person speaking to one specific person, in front of everyone they love.</p>
        <p>Ranked US guides from Zola, Joy and independent officiants converge on a <strong>150–250 word</strong> target, which takes roughly one to two minutes to say aloud. The structure below is the four-part version used by most of them.</p>
        <h2>The four-part frame and its word budget</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Part</th><th>What it does</th><th>Share of a 200-word vow</th></tr></thead>
            <tbody>
                <tr><td>1. Open</td><td>Say their actual name and one line about who they are</td><td>~7%</td></tr>
                <tr><td>2. One story</td><td>A single concrete memory — a place, a detail, a moment you knew</td><td>~42%</td></tr>
                <tr><td>3. Three to six promises</td><td>Keepable actions, at least one you could prove next Tuesday</td><td>~40%</td></tr>
                <tr><td>4. Close</td><td>One short line about the life ahead, then stop</td><td>~10%</td></tr>
            </tbody>
        </table></div>
        <p>The promises are the part that separates a vow from a toast. A line with "I will" in it is a promise; a list of qualities is a speech. Officiants quoted in the top-ranking guides suggest three to six of them, and warn that vague ones are where guests switch off.</p>
        <h2>Read it aloud, slowly</h2>
        <p>The word counter above estimates speaking time at 150 words per minute (average US conversation pace) and at 100 wpm (a slow, nervous ceremony pace). Plan for the slower number: pauses, a breath, and a wobble or two will add time. Print the final draft on a card rather than reading it from a phone — several of the ranked guides call this out as the single most repeated practical tip.</p>
        <h2>A note on AI and vows</h2>
        <p>Zola's 2026 First Look Report, covering more than 11,500 couples, found <strong>63% say AI has no place in writing vows</strong>. That is why this is a <em>builder</em>, not a ghostwriter: it supplies the frame, the prompts and the pacing, and you supply every sentence. Nothing is sent to a model or a server. If you want the traditional wording alongside your own, check with your officiant — Catholic, Hindu, Jewish and civil ceremonies all have different rules about what may be added.</p>
        <h2>What comes next</h2>
        <p>Once the vows are drafted, the other words on the day are the <a href="/tools/wedding-speech-writer/">reception speeches</a>. And when the day is over, those words become the audio spine of a <a href="/blog/wedding-video-from-photos/">cinematic wedding film</a> — the reason so many couples choose to record them clearly.</p>
    """,
    "faq": [
        ("How long should wedding vows be?", "Most US guides recommend 150–250 words, which takes about one to two minutes to read aloud. Read at a slower pace than feels natural — nerves speed you up, and a 200-word vow at 100 words per minute takes two minutes."),
        ("What is the basic structure of personal wedding vows?", "Four parts: an opening that says your partner's name, one specific shared memory, three to six concrete promises, and a single closing line about the future. In a 200-word vow the story and promises take roughly 40% each."),
        ("How many couples write their own vows?", "61% of US couples wrote personal or personalised vows according to The Knot's 2026 Real Weddings Study of 10,474 couples — the highest rate recorded, up from 44% in 2019."),
        ("Can I combine traditional vows with personal ones?", "Often yes. A hybrid — a brief personal statement followed by the required traditional wording — is increasingly common and satisfies most liturgical requirements. Check with your officiant: Catholic ceremonies in particular restrict the approved formulations."),
        ("Does this tool use AI to write my vows?", "No. Zola's 2026 First Look Report found 63% of couples believe AI has no place in writing vows. This builder only arranges sentences you type into a proven four-part structure, counts the words, and estimates speaking time. Nothing leaves your browser."),
        ("Should I read my vows from my phone?", "Most officiants and ranked guides recommend a printed card instead. A phone screen reads as a script, glares in outdoor light, and is easy to lose in the moment. Use the Print / PDF button and trim the page to card size."),
    ],
    "cta_title": "Words worth keeping on film.",
    "cta_text": "Vows are the audio spine of a wedding film. Turn your photos and recordings into a 60–90 second cinematic keepsake.",
    "logic": r"""
window.FT_COMPUTE = null;
window.FT_GENERATE = function (v) {
  var name = (v.name || '').trim() || 'my love';
  var memory = (v.memory || '').trim() || 'the first ordinary evening we spent together';
  var quality = (v.quality || '').trim() || 'the way you pay attention to small things';
  var promises = (v.promises || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  if (!promises.length) promises = ['I will show up for the ordinary days.'];
  var tone = v.tone || 'warm';
  var openers = {
    warm: name + ', today I choose you — not for the big moments, but for all the ordinary ones we have not lived yet.',
    formal: name + ', I stand here today to take you as my partner, and to promise you a life built on honesty and patience.',
    short: name + ', I choose you. Every day, on purpose.',
    playful: name + ', I promise to keep choosing you — even when you steal the blankets and deny it.'
  };
  var bridges = {
    warm: 'I keep coming back to this: ',
    formal: 'I have thought often of the moment that told me who you are: ',
    short: '',
    playful: 'Exhibit A, your honour: '
  };
  var story = bridges[tone] + memory.replace(/\.$/, '') + '. That is when I knew, and it is still true.';
  if (tone === 'short') story = memory.replace(/\.$/, '') + '. I knew then.';
  var loveLine = {
    warm: 'I love ' + quality + ' — not as an idea, but as something I get to watch up close.',
    formal: 'I admire ' + quality + ', and I am grateful to build a household around it.',
    short: 'I love ' + quality + '.',
    playful: 'I love ' + quality + ' (and yes, I notice even when you think I do not).'
  }[tone];
  var promiseBlock = promises.map(function (p) { return /^i\s/i.test(p) ? p : 'I promise to ' + p.replace(/^to\s/i, ''); }).join(' ');
  var closers = {
    warm: 'So here is my whole promise: I will be in it, paying attention, with you. Always.',
    formal: 'For all the days ahead, I give you my word.',
    short: 'That is all. I am yours.',
    playful: 'Also, I will always make the coffee. Let us go.'
  };
  var parts = [openers[tone], story, loveLine, promiseBlock, closers[tone]];
  var text = parts.join('\n\n');
  var words = text.trim().split(/\s+/).length;
  var slow = Math.floor(words / 100) + ':' + String(Math.round((words / 100 % 1) * 60)).padStart(2, '0');
  var fast = Math.floor(words / 150) + ':' + String(Math.round((words / 150 % 1) * 60)).padStart(2, '0');
  var target = parseInt(v.length, 10) || 200;
  var verdict = words < target * 0.7 ? 'Short — add one more specific detail to the story.' :
                words > target * 1.35 ? 'Long — cut one promise or tighten the memory.' :
                'Inside the 150–250 word range most officiants recommend.';
  return {
    blocks: [{ title: 'Your vow draft', text: text }],
    stats: [
      { num: words, lbl: 'Words', accent: true },
      { num: fast, lbl: 'At 150 wpm' },
      { num: slow, lbl: 'At 100 wpm' },
      { num: promises.length, lbl: 'Promises' }
    ],
    note: verdict + ' Read it aloud at the slower pace. Every sentence here is built only from words you typed — nothing is generated by a model.',
    text: text
  };
};
window.FT_INIT = function () {
  var again = document.getElementById('ft-again');
  if (again) again.style.display = 'none';
  again.textContent = 'Shuffle the phrasing';
};
""",
})

TOOLS.append({
    "slug": "wedding-speech-writer",
    "name": "Wedding Speech Writer",
    "short": "Speech Writer",
    "title": "Wedding Speech Writer: Best Man, MOH, Parent Toasts (Free)",
    "description": "Free wedding speech builder for best man, maid of honour and parents. Fill in the stories, get a structured 3-5 minute toast with a word count. No signup, browser-side.",
    "keywords": "wedding speech writer, best man speech examples, maid of honor speech template, father of the bride speech, wedding toast generator",
    "og_title": "Free Wedding Speech Writer — Every Role, One Structure",
    "category": "WritingApplication",
    "h1": "Wedding Speech Writer",
    "lede": "Best man, maid of honour, parent or couple — build a warm, specific toast from your own stories, with a live length check before you stand up.",
    "panel_title": "Your speech",
    "result_title": "Your toast",
    "mode": "generator",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-role">Your role</label><select class="ft-select" id="ft-role" data-ft="role"><option value="bestman">Best man</option><option value="moh">Maid / matron of honour</option><option value="parent">Parent of the couple</option><option value="couple">The couple (thank-you toast)</option><option value="officiant">Officiant / host</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-speaker">Your name</label><input class="ft-input" type="text" value="Sam" data-ft="speaker" data-ft-default="Sam"></div>
                    <div class="ft-row-2"><div class="ft-row"><label class="ft-label" for="ft-person">Person you are toasting</label><input class="ft-input" type="text" value="Jordan" data-ft="person" data-ft-default="Jordan"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-partner">Their partner</label><input class="ft-input" type="text" value="Taylor" data-ft="partner" data-ft-default="Taylor"></div></div>
                    <div class="ft-row"><label class="ft-label" for="ft-years">How long you have known them</label><input class="ft-input" type="text" value="18 years" data-ft="years" data-ft-default="18 years"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-story">One PG-rated story (one or two sentences)</label><textarea class="ft-textarea" data-ft="story">We once tried to assemble a bookcase without the instructions and ended up with something that only worked as a very expensive coat rack.</textarea></div>
                    <div class="ft-row"><label class="ft-label" for="ft-change">How they changed after meeting their partner</label><input class="ft-input" type="text" value="he started turning down Friday plans, and would not say why" data-ft="change" data-ft-default="he started turning down Friday plans, and would not say why"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-tone">Tone</label><select class="ft-select" id="ft-tone" data-ft="tone"><option value="warm">Funny and warm</option><option value="sincere">Sincere, no jokes</option><option value="formal">Formal</option><option value="short">Under 60 seconds</option></select></div>""",
    "article": """
        <h2>The speech everyone remembers — for better or worse</h2>
        <p>US and UK guides that rank for this topic agree on the running order: the father of the bride or a parent welcomes, the couple may speak, and <strong>the best man speaks last</strong>. They also agree on length — The Perfect Wedding puts a short toast at 300–750 words / two to five minutes, while UK guides allow five to eight minutes for a best man. Longer than that and the room goes.</p>
        <p>The structure is remarkably consistent across the ranked pages: an opening that earns attention, two or three specific stories about one person, a turn toward the couple, a genuine compliment, and a clear toast that tells the room to raise its glass.</p>
        <h2>What to include, and what to cut</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Do</th><th>Avoid</th></tr></thead>
            <tbody>
                <tr><td>Introduce yourself and say how you know the person</td><td>Opening with a dictionary definition of love</td></tr>
                <tr><td>Tell 1–2 true, specific stories with a place and a detail</td><td>Inside jokes only two people understand</td></tr>
                <tr><td>Give the partner a genuine compliment</td><td>Exes, dating-app stories, stag-do secrets</td></tr>
                <tr><td>End on a clear "please raise your glasses"</td><td>Trailing off with "so… yeah, cheers"</td></tr>
                <tr><td>Practise aloud three times; use note cards</td><td>Reading a phone screen, or winging it after the open bar</td></tr>
            </tbody>
        </table></div>
        <p>A useful test from one NYC officiant: if it has no "I will" lines and is addressed to the room, it is a toast, not a vow. If you are writing the vows themselves, use the <a href="/tools/wedding-vow-writer/">vow writer</a> instead — the two forms are easy to confuse and do different jobs.</p>
        <h2>Timing it</h2>
        <p>The live word count above uses 130 words per minute, a comfortable pace for a nervous speaker with pauses for laughter. Build in two to three seconds after each joke — the silence is where the laugh lands. If your draft runs two minutes in practice, expect closer to two and a half on the night.</p>
        <h2>After the wedding</h2>
        <p>Speeches are one of the few parts of the day captured in the couple's own voices. If you are recording them, keep that audio — it is often what turns a <a href="/blog/wedding-video-from-photos/">wedding film</a> from a slideshow into a story. Later, the same guest list drives the <a href="/tools/wedding-thank-you-note-generator/">thank-you notes</a>.</p>
    """,
    "faq": [
        ("How long should a best man speech be?", "Two to five minutes is the most common US guidance (300–750 words); some UK guides allow five to eight. Shorter is almost never a mistake. Practise aloud and time it — a draft that runs two minutes in practice usually takes two and a half live."),
        ("What is the correct order of wedding speeches?", "Traditionally a parent of the couple welcomes guests, the couple may thank everyone, then the maid of honour, then the best man last. Modern weddings reorder freely; confirm the running order with the couple and the DJ or MC."),
        ("What should a wedding speech never include?", "Exes, dating-app stories, stag or hen weekend secrets, jokes at the partner's expense, and inside jokes the room will not understand. Every ranked guide also warns against opening with a dictionary definition of love."),
        ("Do I have to be funny?", "No. Warm and specific beats a stand-up routine. The most reliable structure is one funny story, one sincere story, a genuine compliment to the couple, and a clear final toast."),
        ("Should I read from my phone or from cards?", "Note cards. Several ranked guides call this out explicitly: a phone reads as a script, distracts the room, and is awkward to hold with a glass. Use Print / PDF and cut the page to card size."),
        ("Is anything I type sent to a server?", "No. The speech is assembled in your browser from the words you type. Nothing is uploaded, there is no account, and the draft is saved only in this device's local storage until you clear it."),
    ],
    "cta_title": "Keep the voices, not just the photos.",
    "cta_text": "A wedding film with real vows and real toasts hits differently. Build yours from the photos and audio you already have.",
    "logic": r"""
window.FT_GENERATE = function (v) {
  var role = v.role || 'bestman', speaker = (v.speaker || '').trim() || 'I';
  var person = (v.person || '').trim() || 'my friend';
  var partner = (v.partner || '').trim() || 'their partner';
  var years = (v.years || '').trim() || 'a long time';
  var story = (v.story || '').trim().replace(/\.$/, '') || 'we have collected more stories than either of us can reliably tell';
  var change = (v.change || '').trim().replace(/\.$/, '') || 'they started smiling at their phone in a way none of us had seen before';
  var tone = v.tone || 'warm';
  var intros = {
    bestman: "Good evening. I'm " + speaker + ", and I have the honour of being " + person + "'s best man. I have known them for " + years + ".",
    moh: "Hi everyone. I'm " + speaker + ", " + person + "'s maid of honour. We have been in each other's lives for " + years + ".",
    parent: "Good evening. I'm " + speaker + ", " + person + "'s parent, and on behalf of both families, welcome.",
    couple: "Hello everyone. We are " + person + " and " + partner + ", and we wanted to say one thing before the music starts.",
    officiant: "Good evening. I'm " + speaker + ", and it has been a privilege to be part of this day."
  };
  var joke = {
    warm: "When they asked me to speak, they said 'keep it short and do not embarrass me'. I have decided to take one of those suggestions seriously.",
    sincere: '',
    formal: '',
    short: ''
  }[tone];
  var storyBlock = (role === 'couple')
    ? 'Looking around this room tonight, what we feel most is gratitude. ' + story + '.'
    : story + '. I have a dozen stories like that, but this is the one that fits a room with grandparents in it.';
  var pivot = {
    bestman: 'Then I noticed ' + change + '. That was new, and it was obviously good.',
    moh: 'Then ' + change + '. I had never seen them so settled.',
    parent: 'Watching ' + change + ' has been one of the quiet joys of the last few years.',
    couple: 'We met, and somehow the ordinary parts of life got better.',
    officiant: 'In my work I hear a lot of promises. These two say theirs plainly.'
  }[role];
  var compliment = partner + ', thank you for making ' + person + ' so completely themselves. And to the two of you: you are very good for each other, in the specific, unglamorous ways that actually last.';
  var ending = {
    warm: 'So please, raise your glasses — to ' + person + ' and ' + partner + '. To a marriage full of inside jokes, ordinary Tuesdays, and every good thing you two deserve. Cheers!',
    sincere: 'Please raise your glasses. To ' + person + ' and ' + partner + ' — may you always be this kind to each other. Cheers.',
    formal: 'Ladies and gentlemen, please join me in a toast to the happy couple. To ' + person + ' and ' + partner + '.',
    short: 'To ' + person + ' and ' + partner + '. Cheers!'
  }[tone];
  var parts = [intros[role], joke, storyBlock, pivot, compliment, ending].filter(Boolean);
  if (tone === 'short') parts = [intros[role], pivot, ending];
  var text = parts.join('\n\n');
  var words = text.trim().split(/\s+/).length;
  var minutes = Math.floor(words / 130);
  var seconds = Math.round(((words / 130) - minutes) * 60);
  var timing = minutes + ':' + String(seconds).padStart(2, '0');
  return {
    blocks: [{ title: 'Your toast', text: text }],
    stats: [
      { num: words, lbl: 'Words', accent: true },
      { num: timing, lbl: 'Spoken at 130 wpm' },
      { num: parts.length, lbl: 'Sections' }
    ],
    note: words > 750 ? 'Over the usual five-minute ceiling — cut a story or shorten the pivot.' :
          words < 90 ? 'Very short. That is fine for a welcome toast; add one concrete detail if you want more warmth.' :
          'Inside the two-to-five-minute range. Read it aloud three times, pause two seconds after each laugh, and use note cards.',
    text: text
  };
};
window.FT_INIT = function () {
  var again = document.getElementById('ft-again');
  if (again) { again.style.display = 'none'; again.textContent = 'Rephrase'; }
};
""",
})

TOOLS.append({
    "slug": "wedding-guest-count-calculator",
    "name": "Wedding Guest Count Calculator",
    "short": "Guest Count Calculator",
    "title": "Wedding Guest Count Calculator: How Many Will Actually Come",
    "description": "Free wedding guest count calculator. Forecast real attendance from invites, travel and plus-ones, then get tables, meals and vendor deadlines. No signup, browser-side.",
    "keywords": "wedding guest count calculator, what percentage of wedding guests attend, wedding RSVP calculator, how many guests will attend my wedding, wedding attendance estimator",
    "og_title": "Free Wedding Guest Count Calculator — Real Attendance",
    "category": "FinanceApplication",
    "h1": "Wedding Guest Count Calculator",
    "lede": "Invite 150, feed 120. Forecast the real headcount before RSVPs arrive so catering, seating and the bar order are right the first time.",
    "panel_title": "Your guest list",
    "result_title": "Expected attendance",
    "mode": "calc",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-invites">Guests / households invited</label><input class="ft-input" type="number" min="1" max="2000" value="150" data-ft="invites" data-ft-default="150"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-type">Wedding type</label><select class="ft-select" id="ft-type" data-ft="type"><option value="0.85">Local — under 1 hour (85% yes)</option><option value="0.80">Typical local (80% yes)</option><option value="0.75">Regional — 1–3 hours (75%)</option><option value="0.65">Domestic destination (65%)</option><option value="0.55">International destination (55%)</option><option value="0.75">Weekday wedding (75%)</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-plusone">Share with a plus-one (%)</label><input class="ft-input" type="number" min="0" max="100" value="25" data-ft="plusone" data-ft-default="25"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-kids">Children among attendees (%)</label><input class="ft-input" type="number" min="0" max="100" value="10" data-ft="kids" data-ft-default="10"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-capacity">Venue capacity (optional)</label><input class="ft-input" type="number" min="0" max="2000" value="0" data-ft="capacity" data-ft-default="0"></div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="seats" checked> Add a 10-seat planning buffer</label>""",
    "article": """
        <h2>The number nobody knows until it is too late</h2>
        <p>US planning tools that rank for this question converge on the same figure: <strong>80–85% of invited guests attend a local wedding</strong>, meaning 15–20% decline. MySeatPlan, Wedding Notepad and SimplifyCalc all use 80% as the default local acceptance rate and 50–65% for destination weddings. Nearly everyone who RSVPs yes shows up — no-shows are only 2–5% — so the real uncertainty is in the declines.</p>
        <p>That gap is expensive. Guest count drives the catering bill, chair and table rentals, the cake, the bar order, favors and the seating chart. Order for the invitation count and you overpay; order for a hopeful low number and you run out of chairs.</p>
        <h2>Decline rates by relationship and travel</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Guest group / situation</th><th>Typical decline</th><th>Expected per 100 invited</th></tr></thead>
            <tbody>
                <tr><td>Immediate family</td><td>2–5%</td><td>95–98</td></tr>
                <tr><td>Close friends</td><td>10–15%</td><td>85–90</td></tr>
                <tr><td>Extended family</td><td>15–20%</td><td>80–85</td></tr>
                <tr><td>Coworkers / acquaintances</td><td>20–30%</td><td>70–80</td></tr>
                <tr><td>Local wedding (blended)</td><td>15–20%</td><td>80–85</td></tr>
                <tr><td>Domestic destination (flight)</td><td>30–40%</td><td>60–70</td></tr>
                <tr><td>International destination</td><td>40–60%</td><td>40–60</td></tr>
            </tbody>
        </table></div>
        <p>Travel distance is the single strongest predictor in the ranked guides. Saturday weddings beat Sunday and weekday weddings; holiday weekends cut both ways. Send destination save-the-dates 10–12 months out so guests have time to plan.</p>
        <h2>When vendors need a firm number</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Vendor</th><th>Deadline</th><th>Buffer</th></tr></thead>
            <tbody>
                <tr><td>Venue / caterer (final)</td><td>7–14 days before</td><td>Strict, ±0–5 guests</td></tr>
                <tr><td>Rental chairs / tables</td><td>2–4 weeks before</td><td>+5–10 seats</td></tr>
                <tr><td>Alcohol order</td><td>1–2 weeks before</td><td>+15–20%</td></tr>
                <tr><td>Wedding cake</td><td>2–4 weeks before</td><td>+5–10 servings</td></tr>
                <tr><td>Seating chart print</td><td>1–2 weeks before</td><td>Final RSVPs only</td></tr>
            </tbody>
        </table></div>
        <h2>Working backwards from a venue</h2>
        <p>If the room holds 100 and you want it full, you need roughly 118–125 invitations at a local 80–85% acceptance rate — more for a destination wedding. The reverse figure in the results does that math for you. Once the headcount is settled, feed it into the <a href="/tools/wedding-alcohol-calculator/">alcohol calculator</a>, the <a href="/tools/wedding-cake-serving-calculator/">cake calculator</a> and the <a href="/tools/wedding-seating-chart-maker/">seating chart maker</a>.</p>
    """,
    "faq": [
        ("What percentage of invited guests actually attend a wedding?", "For a local US wedding, 80–85% is the standard planning figure (15–20% decline). Destination weddings typically see 50–70% attendance depending on travel distance. Close family attend at 95%+, while coworkers and acquaintances may be nearer 70%."),
        ("How many invitations should I send for 100 guests?", "At an 80% acceptance rate, about 125 invitations. At 85%, about 118. For a destination wedding at 60%, closer to 167. Always leave a 5–10 seat buffer beyond the estimate for late yes responses."),
        ("How do plus-ones affect the headcount?", "A plus-one roughly doubles that invitation's headcount. If 25% of 150 invited households get a plus-one and 80% accept, that adds about 30 guests. Enter your plus-one share above and the result includes it."),
        ("When do I have to give the caterer a final number?", "Most US caterers want the firm headcount 7–14 days before the wedding, and it is usually strict. Chair rentals need 2–4 weeks, the cake 2–4 weeks, and the seating chart print waits for final RSVPs."),
        ("Should children count as full adult meals?", "Many catering planners weight a child's meal at about 0.6 of an adult portion. The result shows both the headcount and a meal-equivalent figure so you can compare quotes fairly."),
        ("Does a weekday wedding change attendance?", "Yes. Ranked guides put weekday weddings at 20–30% declines versus 10–15% for a local Saturday, because guests need time off work or childcare. Choose the Weekday option in the tool to model it."),
    ],
    "logic": r"""
window.FT_COMPUTE = function (v) {
  var invites = Math.max(1, v.invites || 1);
  var rate = parseFloat(v.type) || 0.80;
  var plus = Math.min(100, Math.max(0, v.plusone || 0)) / 100;
  var kidsPct = Math.min(100, Math.max(0, v.kids || 0)) / 100;
  var primary = invites * rate;
  var plusOnes = invites * plus * rate;
  var total = Math.round(primary + plusOnes);
  var kids = Math.round(total * kidsPct);
  var adults = total - kids;
  var meals = Math.round(adults + kids * 0.6);
  var buffer = v.seats ? 10 : 0;
  var roundTables = Math.ceil((total + buffer) / 8);
  var longTables = Math.ceil((total + buffer) / 10);
  var needed = Math.ceil(invites / rate);
  var capacity = v.capacity || 0;
  var rows = [
    ['Primary guests', Math.round(primary), Math.round(invites - primary) + ' declines'],
    ['Plus-ones attending', Math.round(plusOnes), Math.round(invites * plus) + ' invited'],
    ['Adults / children', adults + ' / ' + kids, kidsPct * 100 + '% children'],
    ['Meal equivalents', meals, 'children weighted at 0.6'],
    ['Round tables (8 per table)', roundTables, 'long tables of 10: ' + longTables],
    ['Invite this many for a target of ' + invites, needed, 'at a ' + Math.round(rate * 100) + '% yes rate']
  ];
  if (capacity > 0) {
    var room = capacity - total;
    rows.push(['Venue capacity ' + capacity, room >= 0 ? room + ' seats spare' : Math.abs(room) + ' over capacity',
      room >= 0 ? 'consider a B-list' : 'trim the list or find a larger room']);
  }
  var lines = ['Wedding guest count estimate', invites + ' invited x ' + Math.round(rate * 100) + '% acceptance', ''];
  rows.forEach(function (r) { lines.push(r[0] + ': ' + r[1] + ' — ' + r[2]); });
  lines.push('', 'Vendor deadlines: rentals 2–4 weeks, cake 2–4 weeks, caterer final 7–14 days, alcohol 1–2 weeks.');
  return {
    stats: [
      { num: total, lbl: 'Expected guests', accent: true },
      { num: Math.round(invites - primary), lbl: 'Declines' },
      { num: roundTables, lbl: 'Round tables' },
      { num: meals, lbl: 'Meal equivalents' }
    ],
    head: ['Line', 'Value', 'Note'], rows: rows,
    note: 'Planning rules of thumb from US RSVP guidance, not survey data. Re-run this as real RSVPs arrive and give the caterer a firm number 7–14 days out.',
    text: lines.join('\n')
  };
};
""",
})


# Remaining tool definitions are appended by the second half of this module.
from free_tools_data_b import EXTRA_TOOLS  # noqa: E402
TOOLS.extend(EXTRA_TOOLS)

# Title <= 60 chars, description <= 155 chars (site SEO gate). Kept here so the
# copy stays readable in the tool definitions above while the shipped head
# always satisfies the length rule.
SEO_OVERRIDES = {
    "wedding-alcohol-calculator": {
        "description": "Free wedding alcohol calculator. Enter guests and bar hours for a shopping list of wine, beer, spirits and toast bubbles. US pours. No signup."},
    "wedding-vow-writer": {
        "description": "Free wedding vow builder using the four-part structure US couples use. 150-250 words, tone control, word count and speaking time. No signup."},
    "wedding-speech-writer": {
        "description": "Free wedding speech builder for best man, maid of honour and parents. Structured 3-5 minute toast with a live word count. No signup."},
    "wedding-guest-count-calculator": {
        "description": "Free wedding guest count calculator. Forecast attendance from invites, travel and plus-ones, then get tables, meals and vendor deadlines."},
    "name-change-checklist": {
        "description": "Free name change checklist after marriage. SSA first, then DMV, passport, bank and employer — in the order US agencies require. No signup."},
    "wedding-thank-you-note-generator": {
        "description": "Free wedding thank-you card wording generator. Pick the gift type and tone for a ready-to-copy note, or batch the whole gift list."},
    "wedding-dress-code-decoder": {
        "description": "Free wedding dress code decoder. Pick the invitation wording for what to wear — black tie, cocktail, semi-formal, beach or festive."},
    "wedding-vendor-tipping-calculator": {
        "description": "Free US wedding vendor tipping calculator. Enter vendor bills for a suggested tip per envelope and a total cash figure. Handles service charges."},
    "wedding-cake-serving-calculator": {
        "description": "Free wedding cake calculator. Enter guests for a tier recommendation and exact servings for round or square cakes, US and UK portions."},
    "wedding-day-timeline-generator": {
        "title": "Wedding Day Timeline Generator: Build From Ceremony Time",
        "description": "Free wedding day timeline generator. Enter your ceremony time for a full schedule from hair and makeup to send-off, ready to share with vendors."},
    "wedding-gift-calculator": {
        "description": "Free wedding gift calculator for guests. Get a cash gift range from your relationship, plus-one, travel costs and budget. US etiquette, no signup."},
    "wedding-vendor-questions-checklist": {
        "title": "Questions to Ask Wedding Vendors: Free Checklist"},
}
for _tool in TOOLS:
    if _tool["slug"] in SEO_OVERRIDES:
        _tool.update(SEO_OVERRIDES[_tool["slug"]])


def main() -> None:
    out = []
    for t in TOOLS:
        path = ROOT / "tools" / t["slug"] / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(t), encoding="utf-8", newline="\n")
        out.append(f"{t['slug']:38s} {len(t['faq'])} FAQs  {path.relative_to(ROOT)}")
    print(f"Generated {len(out)} tool pages")
    print("\n".join(out))


if __name__ == "__main__":
    main()
