// Verify BOT_UA_RE + isBot logic added in _middleware.js (2026-07-27).
// Pure logic test — no network, no deploy. Confirms the 302-skip path works
// for known crawlers / preview bots and does NOT affect real users.

const BOT_UA_RE = /(Googlebot|bingbot|Baiduspider|YandexBot|DuckDuckBot|facebookexternalhit|Twitterbot|Slackbot|LinkedInBot|Applebot|Discordbot|TelegramBot|WhatsApp|Pinterestbot|Embedly|Quora Link Preview|SkypeUriPreview)/i;
function isBot(ua) { return BOT_UA_RE.test(ua || ""); }

const cases = [
  // [UA, expected, comment]
  ["Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", true, "Googlebot desktop"],
  ["Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", true, "Googlebot mobile"],
  ["Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)", true, "Bingbot"],
  ["Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)", true, "Yandex"],
  ["facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)", true, "FB preview"],
  ["Twitterbot/1.0", true, "Twitter card"],
  ["Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)", true, "Slack unfurl"],
  ["LinkedInBot/1.0 (compatible; Mozilla/5.0)", true, "LinkedIn"],
  ["Mozilla/5.0 (compatible; Applebot/0.1; +http://www.apple.com/go/applebot)", true, "Applebot (Siri/Spotlight)"],
  ["Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", true, "Discord embed"],
  ["TelegramBot (like TwitterBot)", true, "Telegram"],
  ["WhatsApp/2.21.12.21 A", true, "WhatsApp preview"],
  ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", false, "Real Chrome user"],
  ["Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", false, "Real iPhone Safari"],
  ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", false, "Real Mac Chrome"],
  ["", false, "Empty UA (curl, simple HTTP client)"],
  [undefined, false, "Missing UA header"],
  ["python-requests/2.31.0", false, "Generic Python (not a known crawler)"],
  ["Mozilla/5.0 (compatible; Googlebot-Image/1.0)", true, "Googlebot-Image (variant)"],
  ["Googlebot/2.1 (+http://www.google.com/bot.html)", true, "Googlebot short form"],
];

let pass = 0, fail = 0;
for (const [ua, expected, comment] of cases) {
  const got = isBot(ua);
  const ok = got === expected;
  if (ok) pass++; else fail++;
  console.log(`${ok ? "✓" : "✗"}  isBot(${ua ? ua.slice(0, 60) : "undefined"}) = ${got}  (expected ${expected})  // ${comment}`);
}
console.log(`\n${pass}/${pass + fail} passed`);
process.exit(fail > 0 ? 1 : 0);
