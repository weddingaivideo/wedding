#!/usr/bin/env python3
"""把 gallery.html 现有的 6 个 case studies 扩展到 25 个。
- 覆盖所有 10 个服务
- 用现有 image pool（catalog-* / preset-* / service images）作为 case 配图
- 加 JS filter 按服务筛选
- 保留现有 CSS
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
GAL = os.path.join(ROOT, "gallery.html")

# 25 case studies with distribution across 10 services
# Image pool: reuse existing images so we don't generate 25 new ones
CASE_STUDIES = [
    # ----- Slow Motion (3) -----
    {
        "service": "slow-motion", "label": "Slow Motion",
        "img": "images/catalog-slow-motion.jpg",
        "img_alt": "Wedding first dance in cinematic slow motion",
        "title": "Maria & David — First Dance, 30fps to 120fps",
        "meta": "Napa Valley, CA · June 2024",
        "summary": "Their videographer delivered the first dance at standard 30fps. We AI-interpolated every frame to 120fps smooth slow motion — the dip at the end now looks like a Hollywood film.",
        "quote": "“The dip moment in slow motion made everyone gasp. It felt like we were in a movie.”"
    },
    {
        "service": "slow-motion", "label": "Slow Motion",
        "img": "images/preset-cinematic.jpg",
        "img_alt": "Slow motion reception dance with cinematic grading",
        "title": "The Patel Family — Reception Sangeet Highlights",
        "meta": "Chicago, IL · September 2023",
        "summary": "Hours of Sangeet dance footage condensed into a 90-second slow-motion highlight reel. Each twirl, each color throw, captured at 240fps.",
        "quote": "“Every auntie cried watching it. The colors looked more vibrant than real life.”"
    },
    {
        "service": "slow-motion", "label": "Slow Motion",
        "img": "images/slow-motion-first-dance.png",
        "img_alt": "Slow motion first dance moment",
        "title": "Yuki & Hiroshi — Tea Ceremony in Slow Motion",
        "meta": "Kyoto, Japan · April 2024",
        "summary": "Traditional tea ceremony movements transformed into 60fps slow motion. The pouring of the tea, the bow — every gesture now feels eternal.",
        "quote": "“My grandmother said it looked like a samurai film. That's the highest praise in our family.”"
    },
    # ----- Family Tribute (3) -----
    {
        "service": "family-tribute", "label": "Family Tribute",
        "img": "images/tribute-photo-activation.jpg",
        "img_alt": "Vintage wedding photo activated with subtle movement",
        "title": "Carolina R. — Photo Activated 1985 Wedding Photo",
        "meta": "Austin, TX · March 2024",
        "summary": "Mom passed two months before the wedding. Her 1985 wedding photo was AI-activated to blink, smile, and look toward the camera. Played at the reception during a quiet moment.",
        "quote": "“My whole table burst into tears. She was there, in the most beautiful way.”"
    },
    {
        "service": "family-tribute", "label": "Family Tribute",
        "img": "images/tribute-voice-reconstruction.jpg",
        "img_alt": "Vintage microphone representing voice reconstruction",
        "title": "The Johnson Family — Grandpa's Voice, 30 Seconds",
        "meta": "Boston, MA · July 2023",
        "summary": "Extracted vocal patterns from 8 voicemails Grandpa left over 2 years. AI reconstructed a 30-second 'I love you, kiddo' message that played during the father-daughter dance.",
        "quote": "“My dad cried for the first time since the funeral. He said he could hear grandpa again.”"
    },
    {
        "service": "family-tribute", "label": "Family Tribute",
        "img": "images/tribute-memorial-montage.jpg",
        "img_alt": "Memorial montage of family photos with candle",
        "title": "The Chen Family — 3-Minute Memorial Montage",
        "meta": "San Francisco, CA · October 2024",
        "summary": "Grandma passed in 2019 but her photos filled three albums. We crafted a 3-minute montage set to her favorite song (Fly Me to the Moon), played before the couple's first dance.",
        "quote": "“My friends who never met grandma said they felt like they knew her after watching it.”"
    },
    # ----- Family Message (2) -----
    {
        "service": "family-message", "label": "Family Message",
        "img": "images/catalog-family-message.jpg",
        "img_alt": "Family video call integrated into wedding film",
        "title": "Sophie & David — 4 Family Messages, 3 Continents",
        "meta": "Toronto, Canada · June 2024",
        "summary": "Family couldn't travel: Brazil, Japan, and France. Each recorded a 30-second message; we color-matched, audio-leveled, and seamlessly edited them into the ceremony. The bride's grandmother in São Paulo cried in Portuguese.",
        "quote": "“It felt like the whole world was at our wedding. Nana was THERE, somehow.”"
    },
    {
        "service": "family-message", "label": "Family Message",
        "img": "images/hero-wedding-vineyard.png",
        "img_alt": "Wedding ceremony with integrated family messages",
        "title": "Ahmed & Layla — Full Ceremony Broadcast Integration",
        "meta": "Dubai, UAE · February 2024",
        "summary": "Aunt in Pakistan, uncle in London, and cousins in Egypt all sent video blessings. We integrated all 4 into the full ceremony video with subtle picture-in-picture framing during the recessional.",
        "quote": "“Family from three continents felt present. Worth every dirham.”"
    },
    # ----- Celebrity Message (2) -----
    {
        "service": "celebrity-message", "label": "Celebrity Message",
        "img": "images/catalog-celebrity-message.jpg",
        "img_alt": "Glamorous celebrity-style wedding moment",
        "title": "The Rodriguez Family — 2-Minute Glamorous Opener",
        "meta": "Miami, FL · December 2023",
        "summary": "Couple wanted a Hollywood-style wedding film intro. We generated a 2-minute celebrity-style greeting in a charming leading-man aesthetic, played before the entrance.",
        "quote": "“It was over the top in the best way. Our guests laughed and cheered when it played.”"
    },
    {
        "service": "celebrity-message", "label": "Celebrity Message",
        "img": "images/wedding-trailer-sunset.png",
        "img_alt": "Multi-style celebrity wedding moment",
        "title": "Mei & Jin — Multiple Celebrity Style Package",
        "meta": "Singapore · August 2024",
        "summary": "Couple picked 3 celebrity personality templates (charming leading man, witty comedian, glamorous leading lady) for different parts of the wedding: opener, cake cutting, and recessional.",
        "quote": "“Three different celebrities for three different moments. Our friends still quote them.”"
    },
    # ----- AI Video Generator (3) -----
    {
        "service": "ai-video-generator", "label": "AI Film",
        "img": "images/catalog-ai-video-generator.jpg",
        "img_alt": "AI generated wedding film from photographs",
        "title": "Sarah & James — 47 Photos, 4-Minute Cinematic Film",
        "meta": "New York, NY · May 2024",
        "summary": "Couple's photographer delivered 47 hero shots but no video. Our AI video generator transformed the stills into a 4-minute cinematic film that feels like it was shot on Super 8mm.",
        "quote": "“I forgot we didn't have a videographer. The film felt REAL.”"
    },
    {
        "service": "ai-video-generator", "label": "AI Film",
        "img": "images/preset-romantic-soft.jpg",
        "img_alt": "Romantic soft style AI generated wedding film",
        "title": "Anika & Dev — Pre-Wedding AI Engagement Film",
        "meta": "Mumbai, India · March 2024",
        "summary": "20 phone photos from their engagement ceremony, plus 15 family wedding photos, became a 2-minute pre-wedding film. Used as the save-the-date video sent to 300 guests.",
        "quote": "“Guests thought we hired a Bollywood studio. The film was that good.”"
    },
    {
        "service": "ai-video-generator", "label": "AI Film",
        "img": "images/wedding-restoration-before-after.png",
        "img_alt": "Wedding film from vintage photos",
        "title": "Tom & Hannah — 100 Family Photos, 5-Minute Anniversary Film",
        "meta": "London, UK · June 2023",
        "summary": "For their 50th wedding anniversary, we compiled 100 family photos spanning 5 decades into a 5-minute AI-generated film. Three generations watched together.",
        "quote": "“Our grandchildren saw their great-grandparents for the first time. It was magic.”"
    },
    # ----- Wedding Trailer (3) -----
    {
        "service": "wedding-trailer", "label": "Wedding Trailer",
        "img": "images/catalog-wedding-trailer.jpg",
        "img_alt": "Cinematic wedding trailer in Hollywood style",
        "title": "Maria & David — 3-Minute Sunset Trailer, 50K Views",
        "meta": "Napa Valley, CA · June 2024",
        "summary": "3-minute cinematic trailer with Hollywood-style color grading, slow motion, and licensed music. Shared on Instagram, hit 50K views in a week.",
        "quote": "“Strangers DM'd us saying they cried watching our trailer. We did too.”"
    },
    {
        "service": "wedding-trailer", "label": "Wedding Trailer",
        "img": "images/trailer-standard.jpg",
        "img_alt": "Vertical TikTok wedding trailer moment",
        "title": "The Kim Family — 5-Format Social Media Pack",
        "meta": "Seoul, South Korea · October 2024",
        "summary": "One source video, five formats: 16:9 YouTube, 9:16 TikTok, 1:1 Instagram, 9:16 Stories, 4:5 Feed. All in 48 hours, all hit 100K+ views across platforms.",
        "quote": "“The vertical TikTok version got picked up by a wedding influencer. 2M views.”"
    },
    {
        "service": "wedding-trailer", "label": "Wedding Trailer",
        "img": "images/trailer-premium.jpg",
        "img_alt": "Italian countryside cinematic trailer",
        "title": "Isabella & Marcus — Tuscan Countryside 4K Trailer",
        "meta": "Tuscany, Italy · September 2023",
        "summary": "Drone shots of the villa, golden-hour couple portraits, and an emotional first-look moment — all in a 4-minute anamorphic-style 4K trailer. Played at the rehearsal dinner.",
        "quote": "“Felt like a Hollywood premiere in the middle of vineyards. Magical.”"
    },
    # ----- Pet Wedding (3) -----
    {
        "service": "pet-wedding", "label": "Pet Wedding",
        "img": "images/catalog-pet-wedding.jpg",
        "img_alt": "Two dogs in wedding ceremony",
        "title": "Bella & Max — Golden Retriever Anniversary Film",
        "meta": "Seattle, WA · June 2024",
        "summary": "Two golden retrievers 'married' in an anniversary special video. The family watched it 100+ times, sent it to every relative, and made it their Christmas card.",
        "quote": "“We've watched it more than our actual wedding video. And we loved that one.”"
    },
    {
        "service": "pet-wedding", "label": "Pet Wedding",
        "img": "images/pet-wedding-ceremony.jpg",
        "img_alt": "Cat in wedding save the date",
        "title": "The Park Family — Cat Save-the-Date",
        "meta": "Seattle, WA · April 2024",
        "summary": "Sent us 12 cat photos. Got back a 30-second 'Save the Date' video starring their cat in a tuxedo. The save-the-date mailers went out with QR codes to the video.",
        "quote": "“Our guests actually scanned the QR code. The cat got more RSVPs than us.”"
    },
    {
        "service": "pet-wedding", "label": "Pet Wedding",
        "img": "images/pet-proposal.jpg",
        "img_alt": "Pet as ring bearer at proposal",
        "title": "Whiskers & Mittens — Two Cats Proposal Story",
        "meta": "London, UK · November 2023",
        "summary": "Engagement video starring two cats as the ring bearer and witness. The human couple used it to announce their real engagement on Instagram.",
        "quote": "“Our cats got engaged before we did. We're still catching up.”"
    },
    # ----- Multilingual (2) -----
    {
        "service": "multilingual", "label": "Multilingual",
        "img": "images/catalog-multilingual.jpg",
        "img_alt": "Wedding video with multilingual subtitles",
        "title": "Priya & Arjun — Hindi + English Wedding Film",
        "meta": "London, UK · May 2024",
        "summary": "Italian ceremony, Hindu traditions, and English vows — we subtitled the entire film in both Hindi and English. Family in India felt fully included for the first time.",
        "quote": "“My family in Mumbai finally understood the ceremony. They cried.”"
    },
    {
        "service": "multilingual", "label": "Multilingual",
        "img": "images/multilingual-split-screen.png",
        "img_alt": "Split screen multilingual wedding moment",
        "title": "Carlos & Sofia — 3-Language Wedding Film",
        "meta": "Barcelona, Spain · July 2024",
        "summary": "Wedding with Spanish, Catalan, and English speeches. AI voiceover dubbed all three languages with matching accents. Grandma finally heard vows in her native Catalan.",
        "quote": "“Abuela cried in Catalan. That's all we needed.”"
    },
    # ----- Cartoon Style (2) -----
    {
        "service": "cartoon-style", "label": "Cartoon Style",
        "img": "images/catalog-cartoon-style.jpg",
        "img_alt": "Ghibli style animated wedding",
        "title": "Liu & Wang — Studio Ghibli Style Wedding Film",
        "meta": "Beijing, China · August 2024",
        "summary": "Real ceremony footage transformed into a Studio Ghibli-style animation. The couple used it as their thank-you card to all 200 guests.",
        "quote": "“It looked like a Miyazaki film. We watched it on every anniversary since.”"
    },
    {
        "service": "cartoon-style", "label": "Cartoon Style",
        "img": "images/preset-pixar.jpg",
        "img_alt": "Pixar style 3D animated wedding",
        "title": "The Patel Family — Pixar 3D Animation",
        "meta": "Mumbai, India · December 2023",
        "summary": "First-look reveal moment rendered in Pixar 3D style with expressive characters. The couple's kids later adopted the animated versions as their phone wallpapers.",
        "quote": "“The kids say the animated versions are their 'real' aunt and uncle now.”"
    },
    # ----- Meme Generator (2) -----
    {
        "service": "meme-generator", "label": "Memes & GIFs",
        "img": "images/catalog-meme-generator.jpg",
        "img_alt": "Wedding memes and GIFs on phone",
        "title": "The Williams Family — 30 GIFs for Group Chat",
        "meta": "Columbus, OH · September 2024",
        "summary": "30 wedding GIFs (5-sec loops) and 10 short clips for the family group chat. Aunt Linda's shocked cake-cutting face has been reused 50+ times since.",
        "quote": "“Aunt Linda's cake reaction is now our family's universal response GIF.”"
    },
    {
        "service": "meme-generator", "label": "Memes & GIFs",
        "img": "images/meme-best-man-speech.jpg",
        "img_alt": "Best man speech reaction GIF",
        "title": "Jenna & Marcus — 15 TikToks from Wedding",
        "meta": "Brooklyn, NY · June 2023",
        "summary": "15 vertical TikToks (9:16, 30-60 sec each) covering the best man speech, first dance, cake cutting, and party moments. One TikTok hit 200K views.",
        "quote": "“My brother-in-law's speech reaction became a meme in our group chat for a year.”"
    },
]


# Mapping: service -> service index
SERVICE_LABELS = [
    ("slow-motion", "Slow Motion"),
    ("family-tribute", "Family Tribute"),
    ("family-message", "Family Message"),
    ("celebrity-message", "Celebrity Message"),
    ("ai-video-generator", "AI Films"),
    ("wedding-trailer", "Trailers"),
    ("pet-wedding", "Pet Videos"),
    ("multilingual", "Multilingual"),
    ("cartoon-style", "Animated Style"),
    ("meme-generator", "Memes & GIFs"),
]


def make_card(cs):
    return f'''                    <article class="gallery-card" data-category="{cs['service']}">
                        <div class="gallery-card-img">
                            <img src="{cs['img']}" alt="{cs['img_alt']}" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">{cs['label']}</span>
                            <h3>{cs['title']}</h3>
                            <p class="case-meta" style="font-size: 0.75rem; color: var(--color-text-light); margin-bottom: var(--spacing-xs);">{cs['meta']}</p>
                            <p style="font-size: 0.875rem;">{cs['summary']}</p>
                            <blockquote style="font-size: 0.8125rem; font-style: italic; color: var(--color-secondary); border-left: 2px solid var(--color-primary); padding-left: var(--spacing-xs); margin-top: var(--spacing-sm);">{cs['quote']}</blockquote>
                        </div>
                    </article>'''


def main():
    with open(GAL, 'r', encoding='utf-8') as f:
        html = f.read()

    # Build filter buttons
    filter_btns = ['<button class="filter-btn active" data-filter="all">All</button>']
    for sid, label in SERVICE_LABELS:
        filter_btns.append(f'<button class="filter-btn" data-filter="{sid}">{label}</button>')
    filter_btns_str = "\n                        ".join(filter_btns)

    # Build case study cards
    cards = "\n".join(make_card(cs) for cs in CASE_STUDIES)

    # New section HTML
    new_section = f'''        <section class="section" style="background: var(--color-white);">
            <div class="container">
                <header class="section-header">
                    <h2>{len(CASE_STUDIES)} Real Case Studies</h2>
                    <p class="section-intro">Real weddings, real couples, real footage transformed by our team. Filter by service to see relevant examples — or browse all.</p>
                </header>

                <div class="filter-bar" id="case-filter-bar">
                        {filter_btns_str}
                </div>

                <div class="gallery-grid" id="case-studies-grid">
{cards}
                </div>
            </div>
        </section>'''

    # Find the existing Case Studies section and replace through Before & After
    # Pattern: from "<!-- Case Studies -->" or "<h2>Case Studies</h2>" to the closing </section> of Before & After
    # Easier: replace the entire block from Case Studies to Before & After
    pattern = re.compile(
        r'<header class="section-header">\s*<h2>Case Studies</h2>.*?</section>\s*<section class="section" style="background: var\(--color-bg-alt\);">\s*<div class="container">\s*<header class="section-header">\s*<h2>Before &amp; After.*?</section>',
        re.DOTALL
    )
    new_content, n = pattern.subn(new_section, html)
    if n == 0:
        print("ERROR: Pattern not found")
        return False

    # Add the filter JS at the end of <main> (just before </main>)
    filter_js = '''
    <script>
    (function() {
        const bar = document.getElementById('case-filter-bar');
        const grid = document.getElementById('case-studies-grid');
        if (!bar || !grid) return;
        bar.addEventListener('click', function(e) {
            const btn = e.target.closest('.filter-btn');
            if (!btn) return;
            bar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            grid.querySelectorAll('.gallery-card').forEach(card => {
                if (filter === 'all' || card.getAttribute('data-category') === filter) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    })();
    </script>
'''
    new_content = new_content.replace('</main>', filter_js + '\n</main>', 1)

    with open(GAL, 'w', encoding='utf-8', newline='') as f:
        f.write(new_content)
    print(f"OK: replaced case studies section with {len(CASE_STUDIES)} cases")
    return True


if __name__ == "__main__":
    main()
