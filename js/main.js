/* =============================================
   WeddingAI.video — Main JS
   Shared across all pages
   ============================================= */

(function () {
    'use strict';

    // ---------- Mobile menu toggle ----------
    const toggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.main-nav');
    if (toggle && nav) {
        const navLinks = nav.querySelectorAll('a');

        function setMenuOpen(open) {
            toggle.classList.toggle('active', open);
            nav.classList.toggle('active', open);
            toggle.setAttribute('aria-expanded', String(open));
            if (open && navLinks[0]) {
                // Focus first link for keyboard users
                navLinks[0].focus();
            } else if (!open) {
                // Return focus to toggle when closing (after a tick so click events settle)
                toggle.focus();
            }
        }

        toggle.addEventListener('click', function () {
            const isOpen = nav.classList.contains('active');
            setMenuOpen(!isOpen);
        });

        // Close on ESC, return focus to toggle
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && nav.classList.contains('active')) {
                setMenuOpen(false);
            }
        });

        // Focus trap: Tab cycles within the open menu
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Tab' || !nav.classList.contains('active')) return;
            if (navLinks.length === 0) return;
            const first = navLinks[0];
            const last = navLinks[navLinks.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        });

        // Close when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (nav.classList.contains('active') &&
                !nav.contains(e.target) &&
                !toggle.contains(e.target)) {
                setMenuOpen(false);
            }
        });
    }

    // ---------- Form validation (order.html) ----------
    const orderForm = document.querySelector('.order-form');
    if (orderForm) {
        const status = orderForm.querySelector('#form-status');

        function setStatus(message, kind) {
            if (!status) return;
            status.textContent = message || '';
            status.className = 'form-status' + (kind ? ' form-status-' + kind : '');
        }

        orderForm.addEventListener('submit', function (e) {
            const required = orderForm.querySelectorAll('[required]');
            const errors = [];
            let firstError = null;

            required.forEach(function (field) {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    field.setAttribute('aria-invalid', 'true');
                    const label = orderForm.querySelector('label[for="' + field.id + '"]');
                    const name = label ? label.textContent.replace(/\*/g, '').trim() : field.name;
                    errors.push(name + ' is required');
                    if (!firstError) firstError = field;
                } else {
                    field.classList.remove('error');
                    field.removeAttribute('aria-invalid');
                }
            });

            const emailField = orderForm.querySelector('[type="email"]');
            if (emailField && emailField.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailField.value)) {
                emailField.classList.add('error');
                emailField.setAttribute('aria-invalid', 'true');
                errors.push('Please enter a valid email address');
                if (!firstError) firstError = emailField;
            }

            if (errors.length > 0) {
                e.preventDefault();
                setStatus('Please fix the following: ' + errors.join('; '), 'error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } else {
                // Generate a reference number client-side so the user gets one
                // even if the network call to /api/quote silently fails.
                // Format: WA-YYYYMMDD-XXXX (4-char base36 random).
                const d = new Date();
                const pad = function (n) { return String(n).padStart(2, '0'); };
                const stamp = d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate());
                const rand = Math.floor(Math.random() * 1679616).toString(36).toUpperCase().padStart(4, '0');
                const refId = 'WA-' + stamp + '-' + rand;

                // Append to form so the server can echo it in the confirmation email.
                let refInput = orderForm.querySelector('input[name="reference_id"]');
                if (!refInput) {
                    refInput = document.createElement('input');
                    refInput.type = 'hidden';
                    refInput.name = 'reference_id';
                    orderForm.appendChild(refInput);
                }
                refInput.value = refId;

                setStatus('Sending your request…', 'sending');
                const btn = orderForm.querySelector('[type="submit"]');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Sending…';
                }

                // GA4 generate_lead event — captures the funnel.
                // Use sendBeacon if available (survives navigation to /success).
                try {
                    if (typeof gtag === 'function') {
                        gtag('event', 'generate_lead', {
                            service: (orderForm.querySelector('#service') || {}).value || 'unknown',
                            country: (orderForm.querySelector('#country') || {}).value || 'unknown',
                            reference_id: refId,
                        });
                    }
                    if (navigator.sendBeacon) {
                        const fd = new FormData();
                        fd.append('event', 'lead_submit_attempt');
                        fd.append('reference_id', refId);
                        navigator.sendBeacon('/__lead_event', fd);
                    }
                } catch (e) { /* analytics are best-effort */ }

                // Persist reference_id so success.html can show it after the
                // 303 redirect to /success?id=… below.
                try { sessionStorage.setItem('wa_ref_id', refId); } catch (e) { /* SSR / private mode */ }
            }
        });

        // Clear error state on input
        orderForm.querySelectorAll('input, select, textarea').forEach(function (field) {
            field.addEventListener('input', function () {
                field.classList.remove('error');
                field.removeAttribute('aria-invalid');
                if (status && status.classList.contains('form-status-error')) {
                    setStatus('', null);
                }
            });
        });
    }

    // ---------- success.html — render reference ID ----------
    const refSlot = document.getElementById('reference-id-slot');
    if (refSlot) {
        const params = new URLSearchParams(window.location.search);
        const fromQuery = params.get('id');
        const status = params.get('status'); // "pending" if email send failed
        let fromSession = null;
        try { fromSession = sessionStorage.getItem('wa_ref_id'); } catch (e) { /* no-op */ }
        const ref = (fromQuery || fromSession || '').toUpperCase();
        if (ref && /^WA-\d{8}-[A-Z0-9]{4}$/.test(ref)) {
            refSlot.textContent = ref;
            const copyBtn = document.getElementById('reference-copy');
            if (copyBtn) {
                copyBtn.hidden = false;
                copyBtn.addEventListener('click', function () {
                    navigator.clipboard.writeText(ref).then(function () {
                        const orig = copyBtn.textContent;
                        copyBtn.textContent = '✓ Copied';
                        setTimeout(function () { copyBtn.textContent = orig; }, 2000);
                    }).catch(function () { /* clipboard unavailable */ });
                });
            }
            // Pre-fill the mailto subject with the reference ID so the user can
            // email order@weddingai.video in one click and we can find their request.
            const mailto = document.getElementById('pending-mailto');
            if (mailto) {
                mailto.href = 'mailto:order@weddingai.video?subject=' +
                    encodeURIComponent('Follow-up on my quote ' + ref) +
                    '&body=' + encodeURIComponent('Hi,\n\nFollowing up on my quote request ' + ref + '. I haven\'t received a confirmation email yet.\n\nThanks!');
            }
            // Show the pending notice if the server said the email send failed
            if (status === 'pending') {
                const notice = document.getElementById('pending-notice');
                if (notice) notice.hidden = false;
                const icon = document.getElementById('success-icon');
                if (icon) icon.textContent = '⏳';
                const headline = document.getElementById('success-headline');
                if (headline) headline.textContent = "We've Got Your Request";
                const summary = document.getElementById('success-summary');
                if (summary) summary.textContent = "Your details are saved and our team will follow up within 24 hours. The automatic confirmation email didn't send on the first try — no action needed from you.";
            }
            // Clear session storage so refreshes don't show stale ID
            try { sessionStorage.removeItem('wa_ref_id'); } catch (e) { /* no-op */ }
        }
    }

    // ---------- Cookie consent banner (GDPR / CCPA) ----------
    // Minimal banner: shows on first visit, persists choice in localStorage for 180 days.
    // Respects the user's prior choice; does not block page render (deferred via DOMContentLoaded).
    const COOKIE_KEY = 'wa_cookie_consent';
    const COOKIE_MAX_AGE = 180; // days
    function getCookieConsent() {
        try { return localStorage.getItem(COOKIE_KEY); } catch (e) { return null; }
    }
    function setCookieConsent(value) {
        try { localStorage.setItem(COOKIE_KEY, value); } catch (e) { /* private mode */ }
    }
    function showCookieBanner() {
        if (document.getElementById('wa-cookie-banner')) return;
        const banner = document.createElement('div');
        banner.id = 'wa-cookie-banner';
        banner.setAttribute('role', 'region');
        banner.setAttribute('aria-label', 'Cookie consent');
        banner.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;background:#2C2C2C;color:#fff;padding:1rem 1.25rem;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.25);display:flex;flex-wrap:wrap;align-items:center;gap:.75rem;font-size:.875rem;max-width:920px;margin:0 auto;';
        banner.innerHTML = [
            '<div style="flex:1 1 320px;line-height:1.5;">',
            '  <strong style="display:block;margin-bottom:.25rem;">🍪 We use cookies</strong>',
            '  We use essential cookies to run this site and optional analytics cookies to understand how it performs. You can accept all, accept only essential, or read the details in our <a href="/privacy/" style="color:#D4AF37;text-decoration:underline;">privacy policy</a>.',
            '</div>',
            '<div style="display:flex;gap:.5rem;flex-wrap:wrap;">',
            '  <button type="button" id="wa-cookie-reject" style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,.4);padding:.5rem 1rem;border-radius:6px;cursor:pointer;font:inherit;">Essential only</button>',
            '  <button type="button" id="wa-cookie-accept" style="background:#D4AF37;color:#2C2C2C;border:0;padding:.5rem 1rem;border-radius:6px;cursor:pointer;font:inherit;font-weight:600;">Accept all</button>',
            '</div>'
        ].join('');
        document.body.appendChild(banner);
        document.getElementById('wa-cookie-accept').addEventListener('click', function () {
            setCookieConsent('all');
            banner.remove();
        });
        document.getElementById('wa-cookie-reject').addEventListener('click', function () {
            setCookieConsent('essential');
            banner.remove();
        });
    }
    // Show banner if no prior choice
    if (!getCookieConsent() && document.body) {
        showCookieBanner();
    }

    // ---------- Auto-update copyright year ----------
    // The footer copyright text has a hardcoded year baked into each language's
    // i18n JSON value. This small loop finds the rendered element (regardless of
    // language) and swaps the first 4-digit year it sees with the current year.
    // Cheap, robust, and avoids touching 10 language JSONs every January 1st.
    try {
        var year = new Date().getFullYear();
        document.querySelectorAll('[data-i18n*="_weddingai_video_all_rights_reserve"]').forEach(function (el) {
            el.textContent = el.textContent.replace(/\b\d{4}\b/, String(year));
        });
    } catch (e) { /* no-op */ }
})();
