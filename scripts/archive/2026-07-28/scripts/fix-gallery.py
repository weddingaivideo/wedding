import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
path = os.path.join(ROOT, "gallery.html")
content = open(path, encoding="utf-8").read()
orig = content

# Replace the single gallery section with two sub-sections
# We'll restructure: section 1 = Case Studies (creative: ai-film, trailer, pet, ai-film)
#                   section 2 = Before & After (restoration cases)

# Define the new structure
new_gallery = '''<section class="section" style="background: var(--color-white);">
            <div class="container">
                <header class="section-header">
                    <h2>Case Studies</h2>
                    <p class="section-intro">A selection of recent projects across our creative services — AI films, trailers, pet videos, and animated styles.</p>
                </header>

                <div class="filter-bar">
                    <button class="filter-btn active" data-filter="All">All</button>
                    <button class="filter-btn" data-filter="AI Films">AI Films</button>
                    <button class="filter-btn" data-filter="Wedding Trailers">Wedding Trailers</button>
                    <button class="filter-btn" data-filter="Pet Weddings">Pet Videos</button>
                    <button class="filter-btn" data-filter="Cartoon Style">Animated Style</button>
                </div>

                <div class="gallery-grid" id="gallery-creative">
                    <article class="gallery-card" data-category="ai-film">
                        <div class="gallery-card-img">
                            <img src="images/ai-video-generator-workspace.png" alt="AI-generated wedding film" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">AI Film</span>
                            <h3>Sarah &amp; James — AI-Generated Film</h3>
                            <p>Created a full cinematic film from 47 still photographs using our AI video generator. The result felt like a real film, not a slideshow.</p>
                        </div>
                    </article>

                    <article class="gallery-card" data-category="trailer">
                        <div class="gallery-card-img">
                            <img src="images/wedding-trailer-sunset.png" alt="Cinematic wedding trailer" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">Cinematic Trailer</span>
                            <h3>Maria &amp; David — Sunset Trailer</h3>
                            <p>3-minute cinematic trailer with Hollywood-style color grading, slow motion, and licensed music. Shared on social, got 50K views in a week.</p>
                        </div>
                    </article>

                    <article class="gallery-card" data-category="pet">
                        <div class="gallery-card-img">
                            <img src="images/pet-wedding-golden-retrievers.png" alt="Pet wedding video" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">Pet Celebration</span>
                            <h3>Bella &amp; Max — Golden Retriever Wedding</h3>
                            <p>Two golden retrievers "married" in an anniversary special video. The family watched it 100+ times, sent it to every relative.</p>
                        </div>
                    </article>

                    <article class="gallery-card" data-category="ai-film">
                        <div class="gallery-card-img">
                            <img src="images/cartoon-ghibli-style.png" alt="Cartoon-style wedding video" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">Animated Style</span>
                            <h3>Liu &amp; Wang — Ghibli-Style Animation</h3>
                            <p>Real ceremony footage transformed into a Studio Ghibli-style animation. The couple used it as their thank-you card to guests.</p>
                        </div>
                    </article>
                </div>
            </div>
        </section>

        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container">
                <header class="section-header">
                    <h2>Before &amp; After — Restoration Case Studies</h2>
                    <p class="section-intro">Damaged or degraded footage brought back to life. Each pair shows the source clip and the restored, watchable result.</p>
                </header>

                <div class="gallery-grid" id="gallery-restoration">
                    <article class="gallery-card" data-category="restoration">
                        <div class="gallery-card-img">
                            <img src="images/wedding-restoration-before-after.png" alt="1987 VHS restoration before and after" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">VHS Restoration</span>
                            <h3>1987 Footage — VHS to 4K</h3>
                            <p>Damaged VHS tape from 1987 brought back to crisp, watchable HD quality. The Williams family could finally share their ceremony with their grandchildren.</p>
                        </div>
                    </article>

                    <article class="gallery-card" data-category="restoration">
                        <div class="gallery-card-img">
                            <img src="images/family-tribute-hologram.png" alt="Family tribute in wedding video" loading="lazy">
                        </div>
                        <div class="gallery-card-body">
                            <span class="meta">Family Tribute</span>
                            <h3>The Patel Ceremony — Honoring Late Grandfather</h3>
                            <p>Created a respectful tribute segment featuring the groom's late grandfather, using archived photos and audio. One of the most emotional moments of the day.</p>
                        </div>
                    </article>
                </div>
            </div>
        </section>'''

# Find the existing single gallery section and replace
pattern = re.compile(
    r'<section class="section" style="background: var\(--color-white\);">\s*'
    r'<div class="container">\s*'
    r'<div class="filter-bar">.*?</div>\s*</div>\s*</section>',
    re.DOTALL
)
new_content, count = pattern.subn(new_gallery, content)

if count == 0:
    print("ERROR: pattern not found")
else:
    open(path, "w", encoding="utf-8", newline="").write(new_content)
    print(f"  ✓ gallery.html: split into 2 sections (Case Studies + Before & After)")
