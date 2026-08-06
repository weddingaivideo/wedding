$cssPath = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\styles.css"
$existing = Get-Content $cssPath -Raw

$newCSS = @"

/* ---------- PAGE HERO SMALL (service pages) ---------- */
.page-hero-small { min-height: 45vh; }

/* ---------- SECTION VARIANTS ---------- */
.section-dark { background: var(--color-secondary); color: #fff; }
.section-dark h2, .section-dark h3 { color: #fff; }

.section-header { text-align: center; margin-bottom: var(--spacing-xl); }
.section-header h2 { font-size: clamp(1.75rem, 3vw, 2.5rem); color: var(--color-secondary); margin-bottom: 0.75rem; }
.section-header p { font-size: 1.0625rem; color: var(--color-text-light); max-width: 640px; margin: 0 auto; }

.section-intro { font-size: 1.0625rem; color: var(--color-text-light); max-width: 680px; margin: 0 auto 2rem; text-align: center; }

.section-cta { text-align: center; padding: var(--spacing-xl) 0; }

/* ---------- CTA SECTION ---------- */
.cta-section { background: var(--color-secondary); padding: 4rem 0; text-align: center; color: #fff; }
.cta-bg { position: relative; }
.cta-overlay { position: absolute; inset: 0; background: rgba(44,44,44,0.6); }
.cta-content { position: relative; z-index: 1; }
.cta-content h2 { color: #fff; margin-bottom: 1rem; }
.cta-content p { color: rgba(255,255,255,0.85); margin-bottom: 2rem; }

/* ---------- SERVICE GROUP (services/index.html) ---------- */
.service-group { padding: var(--spacing-2xl) 0; }
.service-group-header { text-align: center; margin-bottom: var(--spacing-xl); }
.service-group-header h2 { font-size: clamp(1.5rem, 2.5vw, 2.25rem); color: var(--color-secondary); margin-bottom: 0.75rem; }
.service-group-header p { color: var(--color-text-light); font-size: 1.0625rem; max-width: 600px; margin: 0 auto; }
.service-sub-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
.service-sub-card { background: var(--color-white); border-radius: var(--radius-lg); padding: 1.5rem; border: 1px solid var(--color-border); transition: var(--transition); }
.service-sub-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.service-sub-card h3 { font-size: 1.125rem; margin-bottom: 0.5rem; }
.service-sub-card h3 a { color: var(--color-secondary); text-decoration: none; }
.service-sub-card h3 a:hover { color: var(--color-primary); }
.service-sub-card p { font-size: 0.9375rem; color: var(--color-text-light); margin-bottom: 0.75rem; }
.price-hint { font-size: 0.875rem; font-weight: 700; color: var(--color-primary); }

/* ---------- PRICING ---------- */
.pricing-table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
.pricing-row { display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid var(--color-border); font-size: 0.9375rem; }
.pricing-row .label { color: var(--color-text); }
.pricing-row .value { font-weight: 700; color: var(--color-secondary); }
.pricing-row .value.price { color: var(--color-primary); }
.pricing-box { background: var(--color-bg-alt); border-radius: var(--radius-md); padding: 1.25rem; margin: 1rem 0; }
.price { font-size: 2rem; font-weight: 700; color: var(--color-primary); }
.price span { font-size: 1rem; font-weight: 400; color: var(--color-text-light); }

/* ---------- FORM (order.html) ---------- */
.form-section { padding: var(--spacing-2xl) 0; }
.form-wrapper { max-width: 680px; margin: 0 auto; }
.form-header-img { width: 100%; aspect-ratio: 16/6; object-fit: cover; border-radius: var(--radius-lg); margin-bottom: 2rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-group { margin-bottom: 1.25rem; }
.form-group-full { grid-column: 1 / -1; }
.form-group label { display: block; font-weight: 600; font-size: 0.875rem; margin-bottom: 0.375rem; color: var(--color-text); }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.75rem 1rem; border: 1.5px solid var(--color-border); border-radius: var(--radius-md); font-size: 1rem; font-family: inherit; background: var(--color-white); color: var(--color-text); transition: var(--transition); }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(212,175,55,0.15); }
.form-group textarea { resize: vertical; min-height: 120px; }
.form-submit { margin-top: 1.5rem; }
.form-submit .btn { width: 100%; padding: 1rem; font-size: 1.0625rem; }
.form-note { font-size: 0.8125rem; color: var(--color-text-light); margin-top: 0.75rem; text-align: center; }

/* ---------- CONTACT (order.html) ---------- */
.direct-contact { margin-top: 3rem; }
.contact-methods { display: flex; gap: 2rem; flex-wrap: wrap; justify-content: center; }
.contact-method { display: flex; align-items: center; gap: 0.75rem; }
.contact-icon { font-size: 1.5rem; }
.contact-label { font-size: 0.8125rem; color: var(--color-text-light); }
.contact-value { font-weight: 600; color: var(--color-secondary); }

/* ---------- WHY US (order.html) ---------- */
.why-section { background: var(--color-bg-alt); }
.why-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 2rem; margin-top: 2rem; }
.why-item { text-align: center; }
.why-icon { font-size: 2.5rem; margin-bottom: 1rem; }

/* ---------- TEAM (about.html) ---------- */
.team-section { padding: var(--spacing-2xl) 0; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; margin-top: 2rem; }
.team-card { text-align: center; }
.team-avatar { width: 100%; aspect-ratio: 1; border-radius: var(--radius-lg); overflow: hidden; background: var(--color-bg-alt); margin-bottom: 1rem; }
.team-avatar img { width: 100%; height: 100%; object-fit: cover; }
.team-bio { font-size: 0.875rem; color: var(--color-text-light); }
.team-since { font-size: 0.8125rem; color: var(--color-primary); font-weight: 600; margin-top: 0.25rem; }

/* ---------- NUMBERS (about.html) ---------- */
.numbers-section { background: var(--color-primary); padding: var(--spacing-2xl) 0; }
.numbers-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 2rem; text-align: center; }
.number-item {}
.number-value { font-size: 2.5rem; font-weight: 700; color: #fff; }
.number-label { font-size: 0.875rem; color: rgba(255,255,255,0.8); margin-top: 0.25rem; }

/* ---------- STORY (about.html) ---------- */
.story-section { padding: var(--spacing-2xl) 0; }
.story-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 2rem; margin-top: 2rem; }
.story-text h3 { color: var(--color-secondary); margin-bottom: 0.75rem; }
.story-values { list-style: none; padding: 0; margin-top: 1rem; }
.story-values li { padding: 0.5rem 0; border-bottom: 1px solid var(--color-border); font-size: 0.9375rem; }
.value-item { padding: 0.5rem 0; border-bottom: 1px solid var(--color-border); }

/* ---------- GALLERY (gallery.html) ---------- */
.gallery-section { padding: var(--spacing-2xl) 0; }
.gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.gallery-card { border-radius: var(--radius-lg); overflow: hidden; background: var(--color-bg-alt); transition: var(--transition); }
.gallery-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.gallery-card-img { aspect-ratio: 16/9; overflow: hidden; }
.gallery-card-img img { width: 100%; height: 100%; object-fit: cover; }
.gallery-card-body { padding: 1.25rem; }
.gallery-card-body h3 { font-size: 1.125rem; margin-bottom: 0.375rem; }
.gallery-location { font-size: 0.8125rem; color: var(--color-text-light); margin-bottom: 0.5rem; }
.gallery-detail p { font-size: 0.875rem; color: var(--color-text-light); }
.gallery-before-after { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.75rem; }
.gallery-before-after img { width: 100%; aspect-ratio: 16/9; object-fit: cover; border-radius: var(--radius-sm); }
.ba-label { font-size: 0.75rem; font-weight: 700; margin-bottom: 0.25rem; }

/* ---------- TESTIMONIALS (index.html) ---------- */
.testimonials { padding: var(--spacing-2xl) 0; background: var(--color-bg-alt); }
.testimonials-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
.testimonial-card { background: var(--color-white); border-radius: var(--radius-lg); padding: 1.5rem; box-shadow: var(--shadow-sm); }
.testimonial-avatar { width: 48px; height: 48px; border-radius: 50%; overflow: hidden; background: var(--color-bg-alt); margin-bottom: 1rem; }
.testimonial-avatar img { width: 100%; height: 100%; object-fit: cover; }
.stars { color: var(--color-primary); margin-bottom: 0.75rem; }
.social-links { display: flex; gap: 1rem; margin-top: 1rem; }

/* ---------- FAQ (index.html, pet-wedding.html) ---------- */
.faq { padding: var(--spacing-2xl) 0; }
.faq-list { max-width: 720px; margin: 2rem auto 0; }
.faq-item { border-bottom: 1px solid var(--color-border); }
.faq-item summary { padding: 1rem 0; font-weight: 600; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; }
.faq-item summary::after { content: "+"; font-size: 1.5rem; color: var(--color-primary); }
.faq-item[open] summary::after { content: "-"; }
.faq-item p { padding: 0 0 1rem; color: var(--color-text-light); font-size: 0.9375rem; }

/* ---------- PRODUCTS (pet-wedding.html) ---------- */
.products-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
.product-card { background: var(--color-white); border-radius: var(--radius-lg); overflow: hidden; border: 1px solid var(--color-border); }
.product-img { aspect-ratio: 16/9; overflow: hidden; background: var(--color-bg-alt); }
.product-img img { width: 100%; height: 100%; object-fit: cover; }
.product-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-light); font-size: 0.875rem; }
.product-body { padding: 1.25rem; }
.product-price { font-size: 1.25rem; font-weight: 700; color: var(--color-primary); margin-top: 0.75rem; }

/* ---------- LANGUAGES (multilingual.html) ---------- */
.languages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 1rem; margin: 2rem 0; }
.lang-tag { background: var(--color-bg-alt); border-radius: var(--radius-md); padding: 0.75rem; text-align: center; font-size: 0.875rem; font-weight: 600; }

/* ---------- DELIVERY (wedding-trailer.html) ---------- */
.delivery-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
.delivery-card { background: var(--color-bg-alt); border-radius: var(--radius-lg); padding: 1.5rem; text-align: center; }
.delivery-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.comparison-table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
.comparison-table th, .comparison-table td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--color-border); font-size: 0.9375rem; }
.comparison-table th { background: var(--color-bg-alt); font-weight: 700; }
.check { color: #188038; }
.cross { color: #D93025; }

/* ---------- FEATURES (real-time-cut.html) ---------- */
.feature-list { list-style: none; padding: 0; margin: 1.5rem 0; }
.feature-item { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.625rem 0; border-bottom: 1px solid var(--color-border); font-size: 0.9375rem; }
.feature-icon { color: var(--color-primary); font-size: 1.25rem; flex-shrink: 0; }

/* ---------- STEPS (multiple pages) ---------- */
.steps-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
.step-card { background: var(--color-bg-alt); border-radius: var(--radius-lg); padding: 1.5rem; text-align: center; }
.step-number { width: 40px; height: 40px; border-radius: 50%; background: var(--color-primary); color: #fff; font-weight: 700; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; }
.step-content h3 { font-size: 1.0625rem; margin-bottom: 0.5rem; }
.step-content p { font-size: 0.875rem; color: var(--color-text-light); }
.process-steps { counter-reset: steps; }
.process-step { display: flex; gap: 1.5rem; padding: 1.25rem 0; border-bottom: 1px solid var(--color-border); }
.process-step::before { counter-increment: steps; content: counter(steps); min-width: 36px; height: 36px; background: var(--color-primary); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.step-content { flex: 1; }

/* ---------- FORMATS (dv-repair.html) ---------- */
.formats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
.format-item { background: var(--color-bg-alt); border-radius: var(--radius-md); padding: 1rem; text-align: center; }
.format-icon { font-size: 1.75rem; display: block; margin-bottom: 0.5rem; }
.format-name { font-size: 0.875rem; font-weight: 600; }

/* ---------- PRESETS (ai-video-generator.html) ---------- */
.preset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
.preset-card { position: relative; border-radius: var(--radius-md); overflow: hidden; aspect-ratio: 16/9; cursor: pointer; }
.preset-placeholder { width: 100%; height: 100%; background: var(--color-bg-alt); display: flex; align-items: center; justify-content: center; color: var(--color-text-light); font-size: 0.75rem; }
.preset-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: flex-end; padding: 0.75rem; }
.preset-name { color: #fff; font-size: 0.8125rem; font-weight: 600; }

/* ---------- STYLE CARDS (cartoon-style.html) ---------- */
.style-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
.style-card { text-align: center; }
.style-icon { font-size: 3rem; display: block; margin-bottom: 0.75rem; }

/* ---------- SENSITIVITY NOTE (family-tribute.html) ---------- */
.sensitivity-note { background: #FEF3E2; border-left: 4px solid #E67E22; border-radius: 0 var(--radius-md) var(--radius-md) 0; padding: 1rem 1.25rem; font-size: 0.9375rem; color: #7B4000; margin: 1.5rem 0; }

/* ---------- RELATED SERVICES (dv-repair.html) ---------- */
.related-services { margin-top: 3rem; }
.related-card { background: var(--color-bg-alt); border-radius: var(--radius-md); padding: 1.25rem; display: block; text-decoration: none; color: var(--color-secondary); transition: var(--transition); }
.related-card:hover { background: var(--color-primary); color: #fff; }
.related-card h4 { font-size: 1rem; margin-bottom: 0.25rem; }
.related-card p { font-size: 0.8125rem; opacity: 0.8; }

/* ---------- SUCCESS PAGE ---------- */
.success-section { text-align: center; padding: 4rem 0; }
.success-icon { font-size: 4rem; display: block; margin-bottom: 1.5rem; }
.next-steps { max-width: 560px; margin: 2rem auto; text-align: left; }
.next-steps li { padding: 0.75rem 0; border-bottom: 1px solid var(--color-border); font-size: 0.9375rem; }
"@

# Append before final closing brace
if ($existing -match '(\s*}\s*)$') {
    $existing = $existing -replace '(\s*}\s*)$', ''
    $existing = $existing + $newCSS + "`n}"
    Set-Content $cssPath $existing -NoNewline
    Write-Host "CSS appended successfully"
} else {
    Write-Host "Could not find trailing brace"
}
