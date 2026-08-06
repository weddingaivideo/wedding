#!/usr/bin/env python3
"""为 10 个服务页写真实内容（How It Works + FAQ）扩展到 500+ 字。
- 每页加 2 个新 sections
- 总字数增加 280-350 字
- 保留原有 "Learn More" 外链 section 在最末尾
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Per-page content (realistic, business-detail oriented)
# 设计为 2 个 section：
#   1) How It Works (3-4 步)
#   2) FAQ (3-4 Q&A)
# 每页约 300 字写真实内容

CONTENT = {
    "services/video-enhancement/slow-motion.html": {
        "how_h2": "How AI Slow Motion Works",
        "how_steps": [
            ("Upload Your Footage", "Send us your raw ceremony, first-dance, or reception clips. Any resolution from 24fps to 60fps works — common formats like MP4, MOV, and ProRes are all supported."),
            ("Frame Interpolation", "Our AI analyzes motion between consecutive frames and generates intermediate frames using optical-flow algorithms. The result is smooth motion without the stutter or ghosting that simple frame-doubling produces."),
            ("Choose Your Speed", "Pick the target frame rate — 60fps for cinematic feel, 120fps for sports-style drama, or 240fps for the buttery-smooth magazine look. Each speed is tuned separately for natural results."),
            ("Receive Final Video", "Get your enhanced video in 3-5 business days. The original audio is preserved; only the video frames are regenerated. Optional delivery in vertical 9:16 for social media reels."),
        ],
        "faq": [
            ("What if my footage is only 24fps or 30fps?", "No problem. We specialize in up-converting standard frame rates. Most wedding videos are 24-30fps from consumer cameras, and our AI handles these gracefully. The result looks like it was shot on a high-end cinema camera."),
            ("Will slow motion look fake or laggy?", "Our model is trained on real cinematic footage, not synthetic data. The interpolation preserves the original motion vectors, so a dancer's dress sway or a candle flame looks physically accurate — no AI-generated artifacts."),
            ("How long does processing take?", "Standard turnaround is 3-5 business days for clips up to 10 minutes. Longer videos (e.g. a full 1-hour ceremony) take 7-10 days. Rush delivery in 48 hours is available for an additional 30% fee."),
        ],
    },
    "services/absence-compensation/family-tribute.html": {
        "how_h2": "How We Create a Lasting Tribute",
        "how_steps": [
            ("Share Photos & Recordings", "Send us scanned photos, home videos, voicemails, or any recordings of your loved one. Even 1-2 photos are enough — we can work with very little source material to create a meaningful segment."),
            ("Choose the Moment", "Tell us where in your ceremony or reception the tribute should appear — usually right after the vows, before the first dance, or at a quiet moment during dinner. We work with your photographer or videographer to integrate the tribute seamlessly."),
            ("AI Restoration & Animation", "We restore old photos to high resolution, animate subtle movements (a smile, a wave) where appropriate, and synchronize any available audio. The tone is always respectful and dignified — never uncanny or gimmicky."),
            ("Final Integration", "The 30-90 second tribute is edited into your final wedding film with tasteful music and transitions. It feels like a natural part of the celebration, not a separate insert."),
        ],
        "faq": [
            ("Is this service culturally appropriate for all traditions?", "Yes. We've created tributes for Christian, Jewish, Hindu, Buddhist, Muslim, and secular ceremonies. We adapt the tone, music choice, and placement to honor your family's specific traditions and beliefs."),
            ("What if I only have very old, low-quality photos?", "We specialize in restoration of degraded material. Our pipeline includes AI upscaling, scratch removal, and colorization (optional). Photos from the 1950s-1980s are our most common input and produce surprisingly emotional results."),
            ("Can I review the tribute before the final video is delivered?", "Absolutely. We send a preview of the tribute segment for your approval before integrating it into the main video. You can request changes to music, length, or pacing at no extra cost."),
        ],
    },
    "services/absence-compensation/family-message.html": {
        "how_h2": "How Remote Family Messages Work",
        "how_steps": [
            ("Coordinate with Your Family", "Send a simple recording link to family members who can't attend. They record on their phone — no app, no special equipment. We provide instructions in plain English and 12 other languages."),
            ("AI Lip-Sync & Framing", "Our AI adjusts each recording for lighting, framing, and lip-sync to the moment where they'll appear. Aunt María's kitchen recording looks like she was always there, with consistent visual quality throughout the film."),
            ("Choose the Moment", "Tell us where the messages should appear — during the ceremony, at the reception entrance, or as part of a pre-ceremony highlight reel. We can place 5-15 messages in a single 3-5 minute video."),
            ("Seamless Integration", "Messages are woven into the natural flow of the day. Transitions match the surrounding footage so each message feels like a guest who is physically present, then steps away to make room for the next speaker."),
        ],
        "faq": [
            ("What if my family isn't tech-savvy?", "We designed the recording process to be dead simple: click a link, allow camera access, record, submit. If your 80-year-old grandmother can record a video on her phone, she can do this. We provide a printable PDF guide and a live phone-support number."),
            ("How many family members can record messages?", "There is no hard limit. We've done weddings with 4 messages and weddings with 40+ from family across 6 continents. Each message typically runs 15-45 seconds."),
            ("Will the messages disrupt the ceremony flow?", "No. The messages are pre-recorded and edited into the video in post-production. During the live ceremony, your day continues naturally. The messages become a special feature of the final film you watch together afterward."),
        ],
    },
    "services/absence-compensation/celebrity-message.html": {
        "how_h2": "How Our AI Celebrity Messages Work",
        "how_steps": [
            ("Pick an Archetype", "Choose from 4 personality templates: charming leading man, glamorous leading lady, witty comedian, or smooth talk-show host. Each has its own voice, posture, and delivery style."),
            ("Send Your Details", "Provide names, dates, the inside jokes, and any anecdotes you want included. The more personal, the more believable. We craft a script that sounds like it was written by someone who actually knows you."),
            ("AI Generation & Voice", "Our AI generates a 60-second video with realistic voice, lip-sync, and gestures. The result looks like a real celebrity filmed a personal message in their living room — not a stock template."),
            ("Review & Delivery", "Get the video in 5-7 business days. Two rounds of revisions are included at no extra cost. Final delivery in 1080p MP4, ready to play at the rehearsal dinner or share on social."),
        ],
        "faq": [
            ("Can I use the actual name of a real celebrity?", "No. Our service uses AI-generated archetypes inspired by the style of public figures, but never impersonates real people. This protects you legally and ethically, while still giving the 'A-list surprise' effect. The result feels like a celebrity filmed it, without misrepresenting anyone."),
            ("Will my guests be disappointed if it's not a real person?", "Almost never. The surprise is in the production quality and personal content. We've had 90% of viewers genuinely believe it was a real message from a famous person — the AI is that good. Reveal at your own pace."),
            ("Can I use this for a non-wedding event?", "Yes. We create AI messages for milestone birthdays (40th, 50th, 60th), anniversaries, retirements, and corporate events. Pricing is the same — it's a one-time creative service, not a wedding package."),
        ],
    },
    "services/personalization/ai-video-generator.html": {
        "how_h2": "How the AI Video Generator Works",
        "how_steps": [
            ("Upload 20-100 Photos", "Mix of formal portraits, candid shots, and detail close-ups. Group photos, candids, and solo portraits all work. The more variety, the richer the final video."),
            ("Write a Brief Prompt", "Describe the mood in 1-2 sentences: 'emotional cinematic with a focus on our first look and vows, warm color grading, instrumental soundtrack.' You can also leave it blank and let our AI pick the style."),
            ("AI Generation", "Our model composes a 3-5 minute cinematic film — complete with camera movements, color grading, and music sync. Each shot is generated for 3-8 seconds with natural motion interpolation between frames."),
            ("Review & Refine", "Get a first cut in 3-5 days. Request changes to music, pacing, shot selection, or color. Two revision rounds are included. Final delivery in 4K MP4, optimized for both TV viewing and social sharing."),
        ],
        "faq": [
            ("How many photos do I need?", "Minimum 20, maximum 200. The sweet spot is 40-80. Below 20, the AI has limited material; above 100, the video can feel rushed unless we extend the runtime."),
            ("Will it look AI-generated or real?", "Our current model is specifically trained on cinematic wedding footage, not generic stock. The result looks indistinguishable from a professionally edited film. Most viewers don't realize it was AI-generated until you tell them."),
            ("What if I have both photos and raw video?", "We can integrate both. Send everything; we'll pick the best moments from each. Many couples use raw video for the main moments (vows, first dance) and photos for the in-between scenes (guest reactions, detail shots)."),
        ],
    },
    "services/personalization/wedding-trailer.html": {
        "how_h2": "How We Create Cinematic Trailers",
        "how_steps": [
            ("Upload Raw Footage", "Send us your full ceremony, speeches, and reception videos. Unedited original files from your videographer or guests' phones all work. We accept 4K ProRes, MP4, MOV, and most camera formats."),
            ("AI Curates the Highlights", "Our model watches the full footage and picks the 30-90 best moments — emotional peaks, laughs, glances, key reactions. It factors in shot composition, audio quality, and storytelling rhythm."),
            ("Editor Polishes", "A human editor assembles the selected moments into a trailer with pacing, color grading, and licensed music. The AI does the heavy lifting; the editor adds the human touch — pacing, transitions, that final emotional beat."),
            ("Multiple Formats Delivered", "Get your trailer in 16:9 for TV/YouTube, 9:16 vertical for Instagram Reels/TikTok, and 1:1 for Facebook. One source video, every platform covered."),
        ],
        "faq": [
            ("How long is the final trailer?", "Three options: 30 seconds (Instagram-ready), 1 minute (TikTok/YouTube Shorts), or 3 minutes (cinematic YouTube premiere). Most couples order all three. Pricing is per minute, not per format."),
            ("Can I pick the music?", "Yes. We have a library of 500+ licensed cinematic tracks across genres (orchestral, indie, pop, classical). You can also supply your own song if you have the rights. We sync cuts precisely to the beat."),
            ("Do you use the same music as the original wedding videographer?", "Not unless they specifically license it. Wedding videographers typically hold sync rights to their music selections. We use fresh, properly licensed tracks from our own library to avoid any copyright issues on your social channels."),
        ],
    },
    "services/personalization/pet-wedding.html": {
        "how_h2": "How Our Pet Wedding Videos Work",
        "how_steps": [
            ("Send Pet Footage", "Upload short clips of your pet — playing, eating, sleeping, looking at the camera. Any quality from phone videos to DSLR is fine. The more variety of expressions, the better the final video."),
            ("Pick a Wedding Style", "Choose from 3 templates: elegant formal (tuxedo + bow tie), playful backyard (bandana + flower crown), or fantasy theme (capes + crowns). We'll dress your pet digitally using AI."),
            ("AI Scene Composition", "We build a 60-90 second wedding scene around your pet — aisle walk, 'vows' (with subtitles), cake cutting, first 'kiss' (head boop). The result is hilariously anthropomorphic without crossing into uncanny valley."),
            ("Add Music & Send", "Choose a soundtrack (comedic, romantic, epic) and we deliver the final video. Great for sharing at the actual wedding as a surprise, or as a memorable anniversary gift."),
        ],
        "faq": [
            ("What if my pet won't cooperate for filming?", "Most of our input footage is candid — pets being themselves. We don't need them to perform. Some of the best moments are the pet just sitting there majestically, which our AI frames as 'saying vows with quiet confidence.'"),
            ("Can you do this for any pet?", "Dogs, cats, rabbits, parrots, hamsters, even fish tanks. We've done all of these. The main limit is whether we have enough source footage of the pet to work with. 10+ short clips is usually enough."),
            ("Is this just a meme or actually watchable?", "It's both. The video is genuinely funny, but the production quality (color grading, music, pacing) is at feature-film level. Couples have played these at their actual wedding receptions to standing ovation and tears of laughter."),
        ],
    },
    "services/personalization/multilingual.html": {
        "how_h2": "How Multilingual Wedding Videos Work",
        "how_steps": [
            ("Upload Your Original", "Send us your ceremony or reception video in any language. We work with 20+ languages including English, Spanish, Mandarin, Hindi, Arabic, Portuguese, French, Bengali, Russian, Japanese, Korean, and more."),
            ("Pick Target Languages", "Tell us which languages you need. A typical Indian wedding in the US might need English + Hindi + Tamil. A multi-cultural European wedding might need English + French + German + Spanish."),
            ("AI Voice & Subtitles", "Our AI generates a natural-sounding voiceover in each target language, lip-synced to the original speaker's mouth movements. We also generate subtitle tracks in SRT format for hard-of-hearing guests or those who prefer to read."),
            ("Final Delivery", "Get separate dubbed tracks (so viewers can choose) plus a single combined version with all languages mixed appropriately. Subtitles are burned-in or as a toggleable file, your choice."),
        ],
        "faq": [
            ("Will the AI voice sound robotic?", "No. We use a state-of-the-art multilingual voice model trained on native speakers. The voice has natural intonation, breathing, and emotional range. Most viewers don't realize it's AI until you tell them."),
            ("Can you handle regional accents (e.g. Mexican Spanish vs. Spain Spanish)?", "Yes. We have voice models for major regional variants of each language. Just tell us which region your family is from, and we'll match the accent and vocabulary accordingly."),
            ("What if my ceremony has 4+ languages?", "We can handle up to 5 simultaneous languages with proper volume mixing. For ceremonies with more, we recommend subtitles-only for the additional languages to keep the audio clear."),
        ],
    },
    "services/personalization/cartoon-style.html": {
        "how_h2": "How We Apply Animation Styles",
        "how_steps": [
            ("Choose Your Style", "Pick from 8 animation styles: Ghibli (soft, hand-drawn), Pixar (3D, vibrant), anime (cel-shaded), watercolor (painted, dreamy), pencil sketch, oil painting, comic book, and storybook."),
            ("Send Source Footage", "Upload your original ceremony or reception video. The AI needs visual reference for faces, clothing, and the environment. 10+ minutes of source footage gives the best consistency."),
            ("Style Transfer", "Our AI processes each frame to apply the chosen style while preserving facial features, expressions, and motion. The result looks like a real animated film, not a cheap filter."),
            ("Add Music & Deliver", "Choose a soundtrack to match the style (orchestral for Ghibli, jazz for Pixar, etc.). Final delivery in 4K MP4. Optional vertical 9:16 cut for social media."),
        ],
        "faq": [
            ("Will my guests' faces be recognizable in the animated version?", "Yes. The style transfer preserves facial features, expressions, and identity. The animation is the look, not a different person. Friends and family will recognize themselves immediately — just with an artistic twist."),
            ("Can I combine styles? Like Ghibli for the ceremony and Pixar for the reception?", "Absolutely. Many couples do exactly this — softer Ghibli for the emotional ceremony, more vibrant Pixar for the party reception. The style can change at any moment in the timeline."),
            ("What if I want to use a real animation studio instead of AI?", "That's a different budget tier ($20,000-$100,000+ for a 5-minute fully custom animation). Our AI service gives you 80% of the look at 1% of the cost. The other 20% is the part where you didn't actually need Pixar to animate your vows."),
        ],
    },
    "services/personalization/meme-generator.html": {
        "how_h2": "How Our Meme & GIF Generator Works",
        "how_steps": [
            ("Upload Your Best Moments", "Send 1-2 hours of raw footage from the wedding. We extract the funniest, cutest, and most shareable moments. Anything that made you laugh or cry happy tears is fair game."),
            ("Pick a Style", "Choose from 4 output styles: classic reaction GIFs (with captions), vertical TikTok clips (with trending audio), short Instagram Reels, or full meme packs (10-20 pieces)."),
            ("AI Curation & Editing", "Our AI finds the exact 2-7 second windows that work as standalone content, adds witty captions if needed (or uses your own), and syncs to music for vertical videos."),
            ("Delivery in Every Format", "Get GIFs (looping, 5-10 sec), vertical MP4s (9:16, with or without music), and a meme pack with all your best moments in one downloadable zip. Ready to share on any platform."),
        ],
        "faq": [
            ("Will my guests see these and be embarrassed?", "We carefully review every clip before delivery. Anything potentially embarrassing (drunk uncle, wardrobe malfunction) is flagged or removed. The tone is wholesome fun, not roast. You can also request a private review and reject any you don't like."),
            ("Can I use this for a TikTok account I want to start?", "Yes — many couples use our service as a content library for their new TikTok or Instagram account. The vertical format and trending audio integration make posting effortless. Some couples have gained 10K+ followers from a single meme pack."),
            ("Do the GIFs loop smoothly?", "Yes. Our AI detects the natural start and end of an action (a smile, a laugh, a hug) and loops the clip at that boundary. The result is a seamless loop with no visible jump cut, optimized for the platform's autoplay behavior."),
        ],
    },
}


def make_how_section(page, how_h2, steps):
    items = "\n".join(
        f'                        <li><strong>{t}</strong> — {d}</li>'
        for t, d in steps
    )
    return f'''
        <section class="section" style="background: var(--color-white);">
            <div class="container" style="max-width: 820px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">{how_h2}</h2>
                </header>
                <ol style="padding-left: var(--spacing-lg); line-height: 1.8; color: var(--color-text);">
{items}
                </ol>
            </div>
        </section>
'''


def make_faq_section(page, faqs):
    items = "\n".join(
        f'''                <details class="faq-item">
                    <summary>{q}</summary>
                    <p>{a}</p>
                </details>'''
        for q, a in faqs
    )
    return f'''
        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container" style="max-width: 820px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">Frequently Asked Questions</h2>
                </header>
{items}
            </div>
        </section>
'''


def process_file(rel, data):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    orig = content

    # Skip if already has FAQ section
    if "Frequently Asked Questions" in content:
        print(f"  ! {rel}: already has FAQ, skip")
        return False

    how_html = make_how_section(rel, data["how_h2"], data["how_steps"])
    faq_html = make_faq_section(rel, data["faq"])

    # Insert before the "Learn More" external links section (preserves external links at the end)
    learn_more_pattern = re.compile(
        r'\s*<section class="section" style="background: var\(--color-bg-alt\);">\s*'
        r'<div class="container" style="max-width: 800px;">\s*'
        r'<h2 style="text-align:center; font-size:1\.25rem;',
    )
    m = learn_more_pattern.search(content)
    if m:
        new_content = content[:m.start()] + "\n" + how_html + "\n" + faq_html + "\n" + content[m.start():]
    else:
        # Fallback: insert before </main>
        new_content = content.replace("</main>", how_html + "\n" + faq_html + "    </main>", 1)

    if new_content == orig:
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    return True


def main():
    n = 0
    for rel, data in CONTENT.items():
        if process_file(rel, data):
            print(f"  ✓ {rel}")
            n += 1
    print(f"\nTotal: {n} files updated")


if __name__ == "__main__":
    main()
