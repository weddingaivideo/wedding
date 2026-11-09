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

    // ---------- Localised runtime copy ----------
    // Some strings are written at runtime, so they cannot live in the
    // dictionary as a plain data-i18n binding: the order form's validation
    // messages, the success page's pending notice, the follow-up e-mail.
    // Pages that need them ship a hidden [data-copy-set] block whose
    // children the middleware has already translated server-side. Reading
    // them from the DOM keeps this shared script from having to load a
    // dictionary - which for some languages is several megabytes.
    function readCopy() {
        const out = {};
        const hosts = document.querySelectorAll('[data-copy-set]');
        hosts.forEach(function (host) {
            host.querySelectorAll('[data-copy]').forEach(function (el) {
                const k = el.getAttribute('data-copy');
                if (k) out[k] = el.textContent;
            });
        });
        return out;
    }
    const COPY = readCopy();
    function copy(key, fallback) {
        const v = COPY[key];
        return (v !== undefined && v !== null && v !== '') ? v : fallback;
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
                    errors.push(copy('required', '{field} is required').replace('{field}', name));
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
                errors.push(copy('invalidEmail', 'Please enter a valid email address'));
                if (!firstError) firstError = emailField;
            }

            if (errors.length > 0) {
                e.preventDefault();
                setStatus(copy('errorPrefix', 'Please fix the following: ') + errors.join(copy('errorSeparator', '; ')), 'error');
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

                setStatus(copy('sending', 'Sending your request…'), 'sending');
                const btn = orderForm.querySelector('[type="submit"]');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = copy('sendingButton', 'Sending…');
                }

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
                        copyBtn.textContent = copy('copied', '✓ Copied');
                        setTimeout(function () { copyBtn.textContent = orig; }, 2000);
                    }).catch(function () { /* clipboard unavailable */ });
                });
            }
            // Pre-fill the mailto subject with the reference ID so the user can
            // email order@weddingai.video in one click and we can find their request.
            const mailto = document.getElementById('pending-mailto');
            if (mailto) {
                mailto.href = 'mailto:order@weddingai.video?subject=' +
                    encodeURIComponent(copy('followupSubject', 'Follow-up on my quote {ref}').replace('{ref}', ref)) +
                    '&body=' + encodeURIComponent(copy('followupBody', 'Hi,\n\nFollowing up on my quote request {ref}. I haven\'t received a confirmation email yet.\n\nThanks!').replace('{ref}', ref));
            }
            // Show the pending notice if the server said the email send failed
            if (status === 'pending') {
                const notice = document.getElementById('pending-notice');
                if (notice) notice.hidden = false;
                const icon = document.getElementById('success-icon');
                if (icon) icon.textContent = '⏳';
                const headline = document.getElementById('success-headline');
                if (headline) headline.textContent = copy('pendingHeadline', "We've Got Your Request");
                const summary = document.getElementById('success-summary');
                if (summary) summary.textContent = copy('pendingSummary', "Your details are saved and our team will follow up within 24 hours. The automatic confirmation email didn't send on the first try — no action needed from you.");
            }
            // Clear session storage so refreshes don't show stale ID
            try { sessionStorage.removeItem('wa_ref_id'); } catch (e) { /* no-op */ }
        }
    }

    // ---------- Cookie consent banner (GDPR / CCPA) ----------
    // MOVED OUT 2026-11-02.
    //
    // This file used to build its OWN hard-coded ENGLISH banner with the id
    // 'wa-cookie-banner'. js/cookie-consent.js builds the LOCALIZED one with
    // the SAME id, and js/cookie-consent.js guards on that id existing
    // (`if (document.getElementById('wa-cookie-banner')) return;`).
    //
    // The <script> order in every page put this file FIRST, and both scripts
    // are `defer`, so they run in document order: this English banner won on
    // every one of the 10 non-English sites. The localized dictionary was
    // still fetched (wasted request) and then thrown away, and the privacy
    // link always pointed at the ENGLISH /privacy/ page.
    //
    // js/cookie-consent.js is now the single source of truth. It is injected
    // on every page by functions/_middleware.js -> injectCookieConsent(),
    // and it fetches /i18n/cookie/<lang>.json for the page's language.
    //
    // Do NOT re-add a banner here. If you need to change the banner, edit
    // js/cookie-consent.js and i18n/cookie/<lang>.json.

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
