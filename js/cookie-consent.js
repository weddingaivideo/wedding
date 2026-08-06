/* =============================================
   WeddingAI.video — Cookie Consent (GDPR/CCPA)
   Minimal banner. Persists in localStorage.
   - First visit: shows banner with Accept all / Essential only
   - Choice stored 180 days
   - Does not block rendering (deferred via defer attribute)
   ============================================= */
(function () {
    'use strict';
    var KEY = 'wa_cookie_consent';
    function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
    function set(v) { try { localStorage.setItem(KEY, v); } catch (e) { /* private mode */ } }
    function dismiss(v) { set(v); var b = document.getElementById('wa-cookie-banner'); if (b) b.remove(); }
    function show() {
        if (document.getElementById('wa-cookie-banner')) return;
        var b = document.createElement('div');
        b.id = 'wa-cookie-banner';
        b.setAttribute('role', 'region');
        b.setAttribute('aria-label', 'Cookie consent');
        b.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;background:#2C2C2C;color:#fff;padding:1rem 1.25rem;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.25);display:flex;flex-wrap:wrap;align-items:center;gap:.75rem;font-size:.875rem;max-width:920px;margin:0 auto;';
        b.innerHTML = '<div style="flex:1 1 320px;line-height:1.5;"><strong style="display:block;margin-bottom:.25rem;">🍪 We use cookies</strong>We use essential cookies to run this site and optional analytics cookies to understand how it performs. See our <a href="/privacy/" style="color:#D4AF37;text-decoration:underline;">privacy policy</a> for details.</div><div style="display:flex;gap:.5rem;flex-wrap:wrap;"><button type="button" id="wa-cookie-reject" style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,.4);padding:.5rem 1rem;border-radius:6px;cursor:pointer;font:inherit;">Essential only</button><button type="button" id="wa-cookie-accept" style="background:#D4AF37;color:#2C2C2C;border:0;padding:.5rem 1rem;border-radius:6px;cursor:pointer;font:inherit;font-weight:600;">Accept all</button></div>';
        document.body.appendChild(b);
        document.getElementById('wa-cookie-accept').addEventListener('click', function () { dismiss('all'); });
        document.getElementById('wa-cookie-reject').addEventListener('click', function () { dismiss('essential'); });
    }
    if (!get() && document.body) show();
})();
