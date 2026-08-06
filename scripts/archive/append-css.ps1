$css = Get-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\styles.css" -Raw

# Append new CSS rules before the final closing brace of the last media query
$newRules = @"

/* ---------- PAGE HERO (service detail pages) ---------- */
.page-hero {
    position: relative;
    min-height: 50vh;
    display: flex;
    align-items: center;
    overflow: hidden;
}

.page-hero-bg {
    position: absolute;
    inset: 0;
}

.page-hero-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        to bottom,
        rgba(44, 44, 44, 0.3) 0%,
        rgba(44, 44, 44, 0.5) 50%,
        rgba(44, 44, 44, 0.7) 100%
    );
}

.page-hero-content {
    position: relative;
    z-index: 1;
    padding: 6rem 0 3rem;
}

.page-hero-content h1 {
    color: #fff;
    font-size: clamp(1.75rem, 4vw, 3rem);
    margin-bottom: 1rem;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.page-hero-content p {
    color: rgba(255,255,255,0.9);
    font-size: 1.125rem;
    max-width: 600px;
}

/* ---------- SPLIT COMPARISON ---------- */
.split-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin: 2rem 0;
}

.split-comparison img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.split-half {
    position: relative;
    background: var(--color-secondary);
    min-height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    padding: 1.5rem;
}

.split-half.before { background: #1a1a1a; }
.split-half.after { background: #f5f5f0; }

.split-label {
    display: block;
    text-align: center;
    font-weight: 700;
    font-size: 0.875rem;
    padding: 0.5rem 1rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
}

.split-half.before .split-label { background: rgba(255,255,255,0.1); color: #fff; }
.split-half.after .split-label { background: var(--color-primary); color: #fff; }

/* ---------- TEAM AVATAR ---------- */
.team-avatar {
    width: 100%;
    aspect-ratio: 1;
    overflow: hidden;
    border-radius: var(--radius-lg);
    background: var(--color-bg-alt);
}

.team-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* ---------- GALLERY ITEMS ---------- */
.gallery-item {
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--color-bg-alt);
}

.gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* ---------- MOBILE FIXES ---------- */
@media (max-width: 767px) {
    .page-hero {
        min-height: 40vh;
    }

    .page-hero-bg img {
        display: block;
    }

    .page-hero-overlay {
        display: block;
    }

    .page-hero-content {
        padding: 5rem 0 2rem;
    }

    .split-comparison {
        grid-template-columns: 1fr;
    }
}
"@

# Remove trailing closing brace, append new rules, then close
if ($css -match '(\s*}\s*)$') {
    $css = $css -replace '(\s*}\s*)$', ''
    $css = $css + $newRules + "`n}"
    Set-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\styles.css" $css -NoNewline
    Write-Host "CSS appended successfully"
} else {
    Write-Host "Could not find trailing brace"
}
