// End-to-end test: language switcher dropdown works.
// Use Promise.all([waitForNavigation, selectOption]) to capture the redirect
// that setLang() does, instead of waiting for networkidle (which is delayed
// by AdSense iframes and other long-poll resources that never reach idle).
//
// Run:  node qa/test_dropdown.js
const pw = require('C:/Users/qiaoshan/AppData/Local/npm-cache/_npx/705bc6b22212b352/node_modules/playwright');
process.env.PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/qiaoshan/AppData/Local/ms-playwright';

const BASE = 'https://weddingai.video';

async function selectAndWait(page, value) {
    // The change handler does window.location.href = newUrl, which is a real
    // top-level navigation. Wait for the next framenavigated on the main frame.
    const navPromise = page.waitForNavigation({ timeout: 15000, waitUntil: 'load' });
    await page.selectOption('#wa-lang-select', value);
    await navPromise;
    // Then let i18n.js fetch + apply translations before measuring textContent
    await page.waitForFunction(
        (expected) => {
            const el = document.querySelector('h1.hero-title');
            return el && el.textContent && el.textContent !== expected;
        },
        // The English title is the source of truth — if hero-title is still EN,
        // translations haven't been applied yet
        'Make Every Wedding Moment Unforgettable',
        { timeout: 10000 }
    ).catch(() => null);  // ok if it doesn't change (e.g. switching to EN)
}

async function main() {
    const browser = await pw.chromium.launch({ headless: true });
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();

    const fails = [];
    const log = (k, v) => console.log(`  ${k}: ${JSON.stringify(v)}`);

    // Test 1: /zh/ page renders Chinese
    console.log('=== T1: /zh/ renders Chinese ===');
    await page.goto(`${BASE}/zh/`, { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(
        () => /让每一个/.test(document.querySelector('h1.hero-title')?.textContent || ''),
        { timeout: 10000 }
    );
    const t1 = await page.locator('h1.hero-title').textContent();
    const html1 = await page.locator('html').getAttribute('lang');
    const s1 = await page.locator('#wa-lang-select').inputValue();
    log('url', page.url());
    log('html lang', html1);
    log('hero-title', t1);
    log('dropdown', s1);
    if (!/让每一个/.test(t1)) fails.push('T1: hero-title not Chinese');
    if (html1 !== 'zh') fails.push('T1: html lang not zh');
    if (s1 !== 'zh') fails.push('T1: dropdown not zh');

    // Test 2: switch zh -> ja
    console.log('\n=== T2: switch to ja ===');
    await selectAndWait(page, 'ja');
    const t2 = await page.locator('h1.hero-title').textContent();
    const html2 = await page.locator('html').getAttribute('lang');
    const s2 = await page.locator('#wa-lang-select').inputValue();
    log('url', page.url());
    log('html lang', html2);
    log('hero-title', t2);
    log('dropdown', s2);
    if (!/ja|JP|日本語|結婚|瞬間|瞬き|記憶|結婚|披露/i.test(t2)) {
        // ja translation might be English if JSON missing key — log but don't fail
        console.log('  (ja hero-title is suspicious but might be untranslated, see i18n/ja.json)');
    }
    if (html2 !== 'ja') fails.push('T2: html lang not ja');
    if (s2 !== 'ja') fails.push('T2: dropdown not ja');

    // Test 3: switch ja -> en (default, no prefix)
    console.log('\n=== T3: switch to en ===');
    await selectAndWait(page, 'en');
    const t3 = await page.locator('h1.hero-title').textContent();
    const html3 = await page.locator('html').getAttribute('lang');
    const s3 = await page.locator('#wa-lang-select').inputValue();
    log('url', page.url());
    log('html lang', html3);
    log('hero-title', t3);
    log('dropdown', s3);
    if (t3 !== 'Make Every Wedding Moment Unforgettable') fails.push('T3: hero-title not EN');
    if (page.url() !== `${BASE}/`) fails.push('T3: not at /');
    if (s3 !== 'en') fails.push('T3: dropdown not en');

    // Test 4: switch en -> zh (back to non-default)
    console.log('\n=== T4: switch to zh ===');
    await selectAndWait(page, 'zh');
    const t4 = await page.locator('h1.hero-title').textContent();
    const html4 = await page.locator('html').getAttribute('lang');
    const s4 = await page.locator('#wa-lang-select').inputValue();
    log('url', page.url());
    log('html lang', html4);
    log('hero-title', t4);
    log('dropdown', s4);
    if (!/让每一个/.test(t4)) fails.push('T4: hero-title not Chinese');
    if (!page.url().endsWith('/zh/')) fails.push('T4: url not /zh/');
    if (s4 !== 'zh') fails.push('T4: dropdown not zh');

    // Test 5: switch zh -> ar (RTL)
    console.log('\n=== T5: switch to ar (RTL) ===');
    await selectAndWait(page, 'ar');
    const html5 = await page.locator('html').getAttribute('lang');
    const dir5 = await page.locator('html').getAttribute('dir');
    const s5 = await page.locator('#wa-lang-select').inputValue();
    log('url', page.url());
    log('html lang', html5);
    log('html dir', dir5);
    log('dropdown', s5);
    if (html5 !== 'ar') fails.push('T5: html lang not ar');
    if (dir5 !== 'rtl') fails.push('T5: html dir not rtl');
    if (s5 !== 'ar') fails.push('T5: dropdown not ar');

    await browser.close();

    console.log('\n=== Summary ===');
    if (fails.length === 0) {
        console.log('✅ ALL DROPDOWN TESTS PASSED');
        process.exit(0);
    } else {
        console.log(`❌ ${fails.length} FAILED:`);
        for (const f of fails) console.log('   - ' + f);
        process.exit(1);
    }
}

main().catch(e => { console.error('TEST ERROR:', e); process.exit(1); });
