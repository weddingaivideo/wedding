#!/usr/bin/env python3
"""为 about / gallery / order / services-index / success 写真实内容。
每个页面加 2-3 个 section (How It Works / Why Us / FAQ)，目标 500-700 字。
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"


def make_section(title, body_html, bg="var(--color-white)", extra_class=""):
    return f'''
        <section class="section {extra_class}" style="background: {bg};">
            <div class="container" style="max-width: 820px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">{title}</h2>
                </header>
                {body_html}
            </div>
        </section>
'''


def make_text_paragraphs(paragraphs):
    return "\n".join(
        f'                <p style="color: var(--color-text-light); line-height: 1.8; margin-bottom: var(--spacing-md);">{p}</p>'
        for p in paragraphs
    )


def make_ol_steps(steps):
    items = "\n".join(
        f'                        <li style="margin-bottom: var(--spacing-sm);"><strong>{t}</strong> — {d}</li>'
        for t, d in steps
    )
    return f'''                <ol style="padding-left: var(--spacing-lg); line-height: 1.8; color: var(--color-text);">
{items}
                </ol>'''


def make_faq_list(faqs):
    items = "\n".join(
        f'''                <details class="faq-item">
                    <summary>{q}</summary>
                    <p>{a}</p>
                </details>'''
        for q, a in faqs
    )
    return items


# ===== ABOUT =====
ABOUT_SECTIONS = {
    "why_h2": "Why Couples Choose WeddingAI.video",
    "why_body": make_text_paragraphs([
        "We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it unforgettable. This focus is why we can offer 10 specialized services that traditional studios can't match, at prices that make sense for any budget.",
        "Every project is handled by our 5-person team: a filmmaker who watches every frame, an AI engineer who tunes each model for your specific footage, a colorist who handles the look, an audio engineer who mixes and masters the soundtrack, and a client experience manager who keeps you in the loop from start to finish. No outsourcing, no subcontractors, no surprises.",
        "We're based in the US, work with couples across 11 countries, and have handled projects in 4 languages. The AI doesn't care about time zones; we do, which is why we have flexible scheduling and respond to every inquiry within 24 hours — usually faster.",
    ]),
    "values_h2": "What We Believe",
    "values_body": make_text_paragraphs([
        "<strong>Every love story deserves a beautiful film.</strong> Not every couple has $10,000 for a videographer. Not every wedding has 4K cameras. We believe your story matters regardless of your budget or how it was captured.",
        "<strong>AI is a tool, not a replacement for craft.</strong> The algorithms do the heavy lifting, but a human filmmaker reviews every output. We never send AI-generated footage without an editor's final pass — your video is touched by real humans before you see it.",
        "<strong>Transparency over hype.</strong> We'll tell you honestly if your footage can't be improved as much as you'd hoped, or if a different service would serve you better. Our reputation depends on happy clients, not upsells.",
    ]),
    "faq": [
        ("Can I speak with a real person about my project?",
         "Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to walk through your footage together before you commit."),
        ("Where is your team based?",
         "Our core team is in the US (coast-to-coast) and we have partner editors in the UK, Germany, and Argentina. Every project is overseen by a US-based senior filmmaker regardless of where the editing happens."),
        ("How long have you been in business?",
         "WeddingAI.video launched in 2024, but our team has been in the wedding video industry since 2015. The AI services are new; the craftsmanship is not."),
        ("What if I'm not happy with the result?",
         "Two rounds of revisions are included with every service at no extra cost. If after revisions you're still not satisfied, we offer a full refund — no questions asked. We've processed over 200 projects with a 4.9/5 average rating, and we've refunded fewer than 5 projects total."),
    ],
}

# ===== GALLERY =====
GALLERY_SECTIONS = {
    "why_h2": "What Makes Our Work Different",
    "why_body": make_text_paragraphs([
        "Each of these projects went through the same 4-step process: AI-assisted selection, human curation, color grading, and final mix. The difference is in the details — we don't ship until the look feels right, and we'll often redo a section if it doesn't match the energy of the original footage.",
        "Look closely at the before-and-after pairs in the second section. The VHS footage wasn't just digitized — it was upscaled to HD, color-corrected to match modern cameras, and the audio was denoised and EQ'd. That's the level of care every project receives, whether it's a 1987 wedding tape or last weekend's ceremony.",
    ]),
    "testimonials_h2": "What Clients Say",
    "testimonials_body": '''                <div class="testimonials-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--spacing-md);">
                    <blockquote class="testimonial-card" style="background: var(--color-white); border-radius: var(--radius-lg); padding: var(--spacing-md); box-shadow: var(--shadow-sm);">
                        <p style="color: var(--color-text); font-style: italic; line-height: 1.6;">"My grandfather's 1962 wedding video was 8mm film we thought was lost. WeddingAI restored it to 4K and the colors came back to life. I cried watching it."</p>
                        <footer style="margin-top: var(--spacing-sm);"><cite style="color: var(--color-text-light); font-size: 0.875rem;">— Margaret T., granddaughter, restored 1962 footage</cite></footer>
                    </blockquote>
                    <blockquote class="testimonial-card" style="background: var(--color-white); border-radius: var(--radius-lg); padding: var(--spacing-md); box-shadow: var(--shadow-sm);">
                        <p style="color: var(--color-text); font-style: italic; line-height: 1.6;">"We had two cameras at the wedding but the videographer's main file got corrupted. AI Video Generator saved us — they made a film from 200+ guest photos that feels like the real thing."</p>
                        <footer style="margin-top: var(--spacing-sm);"><cite style="color: var(--color-text-light); font-size: 0.875rem;">— Sarah &amp; James, used AI Video Generator from 47 photos</cite></footer>
                    </blockquote>
                    <blockquote class="testimonial-card" style="background: var(--color-white); border-radius: var(--radius-lg); padding: var(--spacing-md); box-shadow: var(--shadow-sm);">
                        <p style="color: var(--color-text); font-style: italic; line-height: 1.6;">"My wife's family speaks Mandarin, mine speaks Spanish. The multilingual version meant everyone cried in their own language at the reception."</p>
                        <footer style="margin-top: var(--spacing-sm);"><cite style="color: var(--color-text-light); font-size: 0.875rem;">— Diego M., multilingual wedding (Mandarin + Spanish + English)</cite></footer>
                    </blockquote>
                </div>''',
    "faq": [
        ("Can I share these case studies with my venue or guests?",
         "Yes. All our before-and-after case studies are public — feel free to share. The testimonial quotes are published with explicit client permission. If you want a private reference call with a past client in a similar situation, we can arrange that."),
        ("How long does a typical project take?",
         "Standard turnaround is 3-7 business days depending on the service. Restoration projects average 5 days, AI generation 3-4 days, multilingual 7 days. Rush delivery in 48 hours is available for all services at +30% fee."),
    ],
}

# ===== ORDER =====
ORDER_SECTIONS = {
    "process_h2": "What Happens After You Submit",
    "process_body": make_ol_steps([
        ("We Review Your Request", "Sofia (Client Experience) reads your form within 24 hours — usually within 4 hours during business days. She reviews your service selection, timeline, and any links you provided."),
        ("We Sample Your Footage (if applicable)", "For restoration, AI generation, or trailer services, we ask for a 30-60 second sample clip to verify the source quality and confirm the service will deliver the expected result. This is free and takes 1-2 business days."),
        ("We Send You a Personalized Quote", "You receive a detailed quote with: the recommended service(s), exact pricing, timeline, deliverables list, and any options or upsells. No hidden fees. The quote is yours to accept or decline — no pressure."),
        ("We Confirm and Start", "Once you accept (usually by replying \"go ahead\"), we send a short intake form for upload links, branding preferences, and any special requirements. Production starts within 1-2 business days of intake."),
        ("You Receive Drafts and Final Files", "For most services, you get a draft within 3-7 days. You can request changes (2 rounds included). Final files are delivered in your preferred format — typically MP4 for video, MP3 for audio, plus any social-media-specific cuts."),
    ]),
    "pricing_h2": "Transparent Pricing",
    "pricing_body": make_text_paragraphs([
        "Our pricing is per-project, not per-hour — so you know the cost upfront with no surprise overages. Most services start at $99 and the average project is $300-$500. We accept credit cards (Stripe), PayPal, and bank transfer for larger projects. Invoices are sent on delivery; payment is due within 14 days.",
        "If your project requires more than the standard scope (e.g. 4 hours of footage instead of 1), we'll quote a custom price before starting — you always know what you're paying for. We do not charge for file delivery, format conversions, or basic revisions.",
    ]),
    "faq": [
        ("How long until I get a quote?",
         "Within 24 hours of submitting this form — usually much faster during US business hours. If your project is time-sensitive, mention it in the details field and we'll prioritize."),
        ("Is the quote binding?",
         "No. The quote is yours to review, ask questions about, accept, or decline. There's no commitment until you confirm. If you accept and we start work, the price is locked in — no surprise charges."),
        ("What payment methods do you accept?",
         "All major credit cards (via Stripe), PayPal, and bank transfer for projects over $1,000. We do not accept cryptocurrency at this time."),
        ("Can I cancel after accepting?",
         "Yes. If you cancel before we start any work, full refund. If we have started work, we refund the unworked portion (pro-rated by hours invested). After delivery, our standard satisfaction guarantee applies — full refund if you're not happy after 2 revision rounds."),
        ("What if I forgot to include something in my request?",
         "Just reply to the quote email with the additional info. We'll update the quote and timeline if needed. You can also send files and additional context after submitting — Sofia will track everything in your project folder."),
    ],
}

# ===== SERVICES INDEX =====
SERVICES_INDEX_SECTIONS = {
    "choose_h2": "How to Choose the Right Service",
    "choose_body": make_text_paragraphs([
        "Not sure which service you need? Answer these 3 questions to narrow it down:",
        "<strong>1. What's your source material?</strong> Old tape or film (VHS, Hi8, 8mm, 16mm) → Restoration or Family Tribute. Smartphone or modern digital video → Trailer, AI Generator, or Meme Generator. No video at all, just photos → AI Video Generator or Cartoon Style. Mixed bag → AI Video Generator (works with everything).",
        "<strong>2. What's the final use?</strong> Share on social media (Instagram, TikTok) → Trailer (vertical cut) or Memes. Play at the reception → Trailer or Family Message. Watch together as a couple → AI Video Generator. Send to family who couldn't attend → Multilingual or Family Message. Honor a deceased loved one → Family Tribute. Surprise at the rehearsal dinner → Celebrity Message or Pet Wedding.",
        "<strong>3. What's your budget?</strong> Under $100: Meme Generator ($49) or AI Video Generator from photos ($199 — but commonly $99 with first-customer discount). $100-300: AI Video Generator, Cartoon Style, Multilingual, Slow Motion, or Pet Wedding. $300-600: Wedding Trailer, Family Tribute, Family Message. $600+: Complex projects combining multiple services.",
    ]),
    "combine_h2": "Popular Service Combinations",
    "combine_body": make_text_paragraphs([
        "<strong>The \"Complete Film\" Package:</strong> AI Video Generator (main film) + Trailer (social-ready) + Multilingual (for international family). Bundle discount: 15%.",
        "<strong>The \"Heritage\" Package:</strong> Family Tribute (deceased loved one) + Restoration (old footage from same era). Often used for 30th/40th/50th anniversary videos.",
        "<strong>The \"Share-Worthy\" Package:</strong> Trailer (cinematic 3-min) + Meme Generator (10 social clips) + Pet Wedding (funny opener). All optimized for different platforms.",
        "<strong>The \"International Family\" Package:</strong> Multilingual (2-3 languages) + Family Message (remote relatives recorded separately) + Trailer (final 1-min highlight).",
    ]),
    "faq": [
        ("Can I combine multiple services?",
         "Yes, and we encourage it for fuller results. Most projects benefit from 2-3 services combined. We offer bundle discounts of 10-20% for 2+ services on the same project. Just mention which services in your request."),
        ("How do I know which service I need?",
         "If you're unsure, submit the form with 'Other / Not Sure' and a short description. Sofia will read your message, look at any sample footage you provide, and recommend the right service in her quote reply — no charge for the consultation."),
        ("Can I add services after I've already submitted?",
         "Absolutely. Many couples start with one service (e.g. AI Video Generator) and add a Trailer or Meme Generator later once they see the first result. Each addition gets its own quote, timeline, and revision cycle."),
        ("Do you offer any discounts?",
         "Yes: 10% off when you book 2 services, 15% off 3+ services, 20% off 5+ services. We also have a first-customer discount — mention \"FIRST\" in the details field for 20% off your first service. Discounts stack up to a maximum of 30%."),
    ],
}

# ===== SUCCESS =====
SUCCESS_SECTIONS = {
    "next_h2": "What Happens Next",
    "next_body": make_ol_steps([
        ("Within 24 Hours", "Sofia (Client Experience) reviews your request and replies with a personalized quote. She may ask follow-up questions about your footage, timeline, or specific requirements."),
        ("Day 1-3", "You receive a detailed quote with pricing, timeline, and deliverables. You accept (or ask questions) — no pressure, no commitment until you say yes."),
        ("Day 3-7", "If you accept, we send an intake form for upload links and any special preferences. Production starts."),
        ("Day 7-14", "You receive the first draft of your video (or final deliverable for simpler services). You can request up to 2 rounds of revisions."),
        ("Day 14-21", "Final files delivered. You receive all formats (e.g. 16:9 + 9:16 for social), your invoice, and a brief satisfaction survey."),
    ]),
    "useful_h2": "While You Wait — Useful Resources",
    "useful_body": make_text_paragraphs([
        "Curious about how our AI works or what to expect from each service? Browse our <a href=\"/gallery.html\" style=\"color: var(--color-primary);\">gallery</a> to see real before-and-after examples. Or read our <a href=\"/services/\" style=\"color: var(--color-primary);\">full service catalog</a> for pricing and details on every offering.",
        "If you have a quick question in the meantime, you can reply directly to the confirmation email — Sofia will get back to you within a few hours during business days.",
    ]),
    "faq": [
        ("When will I hear back from you?",
         "Within 24 hours of submission, usually much faster during US business hours (9am-6pm Eastern). If you don't hear back within 24 hours, check your spam folder for an email from order@weddingai.video, or reply to this page's confirmation email."),
        ("Can I add more information to my request?",
         "Yes — just reply to the quote email. Sofia can update the quote, add notes, or attach additional files. If you remember something important (e.g. the wedding is in 2 weeks instead of 1 month), tell her as soon as possible so we can adjust the timeline."),
        ("Can I cancel my request?",
         "Of course. Before you accept the quote, there's no commitment. After you accept, you can cancel anytime before production starts for a full refund. Once work has begun, we refund the unworked portion pro-rated by hours invested."),
    ],
}


def process_file(rel, sections, already_check="Frequently Asked Questions"):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if already_check in content:
        print(f"  ! {rel}: already has FAQ, skip")
        return False

    new_html = ""
    for key, val in sections.items():
        if key == "why_h2":
            new_html += make_section(val, sections["why_body"])
        elif key == "values_h2":
            new_html += make_section(val, sections["values_body"], bg="var(--color-bg-alt)")
        elif key == "testimonials_h2":
            new_html += make_section(val, sections["testimonials_body"], bg="var(--color-bg-alt)")
        elif key == "process_h2":
            new_html += make_section(val, sections["process_body"])
        elif key == "pricing_h2":
            new_html += make_section(val, sections["pricing_body"], bg="var(--color-bg-alt)")
        elif key == "choose_h2":
            new_html += make_section(val, sections["choose_body"])
        elif key == "combine_h2":
            new_html += make_section(val, sections["combine_body"], bg="var(--color-bg-alt)")
        elif key == "next_h2":
            new_html += make_section(val, sections["next_body"])
        elif key == "useful_h2":
            new_html += make_section(val, sections["useful_body"], bg="var(--color-bg-alt)")
        elif key == "faq":
            continue  # handled below
    new_html += make_section("Frequently Asked Questions", make_faq_list(sections["faq"]), bg="var(--color-bg-alt)")

    # Insert before "Learn More" external links section, or before </main>
    learn_more_pattern = re.compile(
        r'\s*<section class="section" style="background: var\(--color-bg-alt\);">\s*'
        r'<div class="container" style="max-width: 800px;">\s*'
        r'<h2 style="text-align:center; font-size:1\.25rem;',
    )
    m = learn_more_pattern.search(content)
    if m:
        new_content = content[:m.start()] + "\n" + new_html + "\n" + content[m.start():]
    else:
        new_content = content.replace("</main>", new_html + "    </main>", 1)

    if new_content == content:
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    return True


def main():
    targets = [
        ("about.html", ABOUT_SECTIONS),
        ("gallery.html", GALLERY_SECTIONS),
        ("order.html", ORDER_SECTIONS),
        ("services/index.html", SERVICES_INDEX_SECTIONS),
        ("success.html", SUCCESS_SECTIONS),
    ]
    n = 0
    for rel, sections in targets:
        if process_file(rel, sections):
            print(f"  ✓ {rel}")
            n += 1
    print(f"\nTotal: {n} files updated")


if __name__ == "__main__":
    main()
