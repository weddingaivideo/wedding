"""Second half of the free-tool page definitions. See gen-free-tools.py for the
US SERP evidence list and the shared page template."""

EXTRA_TOOLS = []

EXTRA_TOOLS.append({
    "slug": "wedding-day-timeline-generator",
    "name": "Wedding Day Timeline Generator",
    "short": "Day-of Timeline",
    "title": "Wedding Day Timeline Generator: Build From Your Ceremony Time",
    "description": "Free wedding day timeline generator. Enter your ceremony time and get the full schedule — hair and makeup to send-off — with a vendor-ready copy. No signup.",
    "keywords": "wedding day timeline generator, wedding timeline template, day of wedding schedule, 4pm ceremony timeline, wedding photography timeline",
    "og_title": "Free Wedding Day Timeline Generator — Ceremony to Send-off",
    "category": "ProductivityApplication",
    "h1": "Wedding Day Timeline Generator",
    "lede": "Your ceremony time is the anchor. Everything else — hair and makeup, first look, photos, dinner, toasts, last dance — is worked backwards and forwards from it.",
    "panel_title": "Your day",
    "result_title": "Your hour-by-hour schedule",
    "mode": "calc",
    "panel": """                    <div class="ft-row-2"><div class="ft-row"><label class="ft-label" for="ft-ceremony">Ceremony start</label><input class="ft-input" type="time" value="16:00" data-ft="ceremony" data-ft-default="16:00"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-length">Ceremony length</label><select class="ft-select" id="ft-length" data-ft="length"><option value="20">20 min</option><option value="30" selected>30 min</option><option value="45">45 min</option><option value="60">60 min</option></select></div></div>
                    <div class="ft-row"><label class="ft-label" for="ft-reception">Reception length (hours)</label><select class="ft-select" id="ft-reception" data-ft="reception"><option value="3">3 hours</option><option value="4" selected>4 hours</option><option value="5">5 hours</option><option value="6">6 hours</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-cocktail">Cocktail hour</label><select class="ft-select" id="ft-cocktail" data-ft="cocktail"><option value="45">45 min</option><option value="60" selected>60 min</option><option value="75">75 min</option></select></div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="firstlook" checked> We are doing a first look</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="golden" checked> Add golden-hour portraits (20 min)</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="toss" checked> Include bouquet / garter toss</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="travel"> 20 min drive between ceremony and reception</label>
                    <p class="ft-hint">The default here is the classic 4pm ceremony used in the free templates on Bespoke Bride and WeddingTimeline.org.</p>""",
    "article": """
        <h2>Why the ceremony time is the anchor</h2>
        <p>The free timeline generators that rank in the US all work the same way: <strong>start at "I do" and build outwards</strong>. Bespoke Bride's generator plans hair and makeup chair-by-chair backwards from the ceremony, then runs the reception forwards in a fixed order. WeddingTimeline.org and DigitalRSVPs ship near-identical 29-row templates covering setup, florist arrival, first look, family photos, guest seating, grand entrance, first dance, toasts, cake cutting, open dancing and the send-off.</p>
        <p>This tool follows that order and flags the conflicts the ranked tools warn about: photos that push the couple's own entrance late, hair and makeup starting in the middle of the night, or a reception too short for the moments you picked.</p>
        <h2>The standard running order</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Block</th><th>Typical duration</th><th>Who needs to know</th></tr></thead>
            <tbody>
                <tr><td>Hair &amp; makeup (per person)</td><td>45–60 min each</td><td>Stylists, wedding party</td></tr>
                <tr><td>Getting dressed + detail shots</td><td>45 min</td><td>Photographer</td></tr>
                <tr><td>First look &amp; couple portraits</td><td>30–45 min</td><td>Photographer, videographer</td></tr>
                <tr><td>Wedding party + family photos</td><td>45–60 min</td><td>Family, wedding party</td></tr>
                <tr><td>Guest arrival / ceremony</td><td>30 min + service</td><td>Ushers, officiant, musicians</td></tr>
                <tr><td>Cocktail hour</td><td>45–60 min</td><td>Bar, caterer, photographer</td></tr>
                <tr><td>Grand entrance → first dance</td><td>15 min</td><td>DJ / MC</td></tr>
                <tr><td>Dinner service</td><td>60–75 min</td><td>Caterer</td></tr>
                <tr><td>Toasts → parent dances → cake</td><td>45 min</td><td>DJ, speakers, photographer</td></tr>
                <tr><td>Open dancing → last dance → exit</td><td>Remaining time</td><td>Everyone</td></tr>
            </tbody>
        </table></div>
        <h2>Three rules the ranked guides repeat</h2>
        <ul>
            <li><strong>Build in 15-minute buffers.</strong> Transitions between ceremony, cocktail hour and reception always take longer than expected.</li>
            <li><strong>Finish hair and makeup 30 minutes before the photographer arrives.</strong> Otherwise the detail shots slip and the whole morning compresses.</li>
            <li><strong>Send the timeline to the DJ, photographer and venue at least five days out.</strong> They will spot conflicts you missed, and one person other than the couple should own the schedule on the day.</li>
        </ul>
        <p>If you are adding a sunset portrait slot, look up the sunset time for your venue's town and date — golden hour moves the photo block, not the ceremony. And if you are still months away, start with the <a href="/tools/wedding-checklist-generator/">month-by-month planning checklist</a> before drilling into the day itself.</p>
    """,
    "faq": [
        ("What time should hair and makeup start for a 4pm ceremony?", "With five people in hair and one stylist plus one makeup artist, most templates start around 9:00am. The generator works backwards from your ceremony time, allowing 45–60 minutes per person and a 30-minute buffer before the photographer arrives."),
        ("Should we do a first look?", "A first look moves couple portraits before the ceremony and frees the cocktail hour for family photos. Skip it and you will need 45–60 minutes of portraits after the ceremony — which pushes dinner later. Toggle it above and compare."),
        ("When should the cake cutting happen?", "Most US timelines place cake cutting about 30 minutes after the dance floor opens, following toasts and parent dances. It is also the photographer's cue that the formal coverage is nearly done."),
        ("How far in advance should I create the day-of timeline?", "Two to four weeks before the wedding, once vendor arrival times and ceremony details are confirmed. Share it with the wedding party and all vendors at least one week before the day."),
        ("Can I give this to my vendors?", "Yes. Copy result produces plain text you can paste into an email, and Print / PDF gives a clean vendor-ready sheet. Name a point person other than the couple to keep the day on schedule."),
        ("What if my reception is at a different venue?", "Enable the 20-minute drive option. Travel time eats the cocktail hour, so either extend cocktail or move family photos before the ceremony — the tool shows the collision in the note under the results."),
    ],
    "cta_title": "The day goes fast. The film stays.",
    "cta_text": "A 60–90 second cinematic wedding film built from your photos — delivered in 48 hours.",
    "logic": r"""
window.FT_COMPUTE = function (v) {
  function parse(t) { var p = (t || '16:00').split(':'); return (parseInt(p[0], 10) || 0) * 60 + (parseInt(p[1], 10) || 0); }
  function fmt(min) { var m = ((min % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); }
  var c = parse(v.ceremony), len = parseInt(v.length, 10) || 30;
  var cocktail = parseInt(v.cocktail, 10) || 60;
  var reception = parseInt(v.reception, 10) || 4;
  var travel = v.travel ? 20 : 0;
  var firstlook = !!v.firstlook;
  var rows = [];
  function add(time, label, who) { rows.push([fmt(time), label, who]); }
  var photoStart = c - (firstlook ? 150 : 60);
  var hmStart = photoStart - 210;
  add(hmStart, 'Hair & makeup begins (staggered, bride last)', 'Stylists + wedding party');
  add(hmStart + 120, 'Venue setup, florist and catering arrival', 'Venue + vendors');
  add(photoStart - 60, 'Getting dressed; photographer shoots details', 'Photographer');
  if (firstlook) {
    add(photoStart, 'First look + couple portraits', 'Couple + photographer');
    add(photoStart + 45, 'Wedding party photos', 'Wedding party');
    add(photoStart + 90, 'Family photos', 'Immediate family');
  } else {
    add(photoStart, 'Wedding party / pre-ceremony portraits', 'Wedding party');
  }
  add(c - 30, 'Guest arrival; ushers seat guests', 'Ushers + officiant');
  add(c, 'Ceremony begins', 'Everyone');
  var after = c + len;
  add(after, 'Ceremony ends; couple exits', 'Everyone');
  if (!firstlook) add(after + 10, 'Family + couple portraits', 'Family + photographer');
  if (travel) add(after + 5, 'Travel to reception venue', 'Couple + wedding party');
  var cockStart = after + 10 + travel;
  add(cockStart, 'Cocktail hour begins', 'Bar + caterer');
  var rStart = cockStart + cocktail;
  if (v.golden) add(rStart - 20, 'Golden-hour portraits (20 min)', 'Couple + photographer');
  add(rStart, 'Guest seating + grand entrance', 'DJ / MC');
  add(rStart + 10, 'First dance', 'Couple');
  add(rStart + 20, 'Welcome toast / blessing', 'Parent or host');
  add(rStart + 30, 'Dinner service', 'Caterer');
  var t = rStart + 105;
  add(t, 'Toasts (best man, maid of honour)', 'Speakers');
  add(t + 20, 'Parent dances', 'Couple + parents');
  add(t + 35, 'Cake cutting', 'Photographer');
  if (v.toss) add(t + 50, 'Bouquet / garter toss', 'DJ');
  add(t + 60, 'Open dancing', 'Everyone');
  var end = rStart + reception * 60;
  add(end - 15, 'Last dance', 'Everyone');
  add(end, 'Grand exit / send-off', 'Everyone');
  add(end + 15, 'Vendor breakdown begins', 'Venue + vendors');
  var lines = ['Wedding day timeline — ceremony ' + fmt(c), ''];
  rows.forEach(function (r) { lines.push(r[0] + '  ' + r[1] + '  [' + r[2] + ']'); });
  lines.push('', 'Build in 15-minute buffers. Send to every vendor 5+ days out. One person (not the couple) owns the schedule.');
  var note = 'Standard US running order. Add 15-minute buffers between major blocks and confirm vendor arrival times. ';
  note += (!firstlook ? 'Without a first look, family portraits land after the ceremony and compress cocktail hour. ' : '');
  note += (travel ? 'The 20-minute transfer is included; consider extending cocktail hour.' : 'Same-venue reception assumed.');
  return {
    stats: [
      { num: fmt(c), lbl: 'Ceremony', accent: true },
      { num: fmt(hmStart), lbl: 'Hair & makeup' },
      { num: fmt(rStart), lbl: 'Reception' },
      { num: fmt(end), lbl: 'Send-off' }
    ],
    head: ['Time', 'What happens', 'Who'], rows: rows,
    note: note, text: lines.join('\n')
  };
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-gift-calculator",
    "name": "Wedding Gift Calculator",
    "short": "Gift Calculator",
    "title": "Wedding Gift Calculator: How Much Should a Guest Give?",
    "description": "Free wedding gift calculator for guests. Get a respectful cash gift range from your relationship, plus-one, travel costs and budget. US etiquette, no signup.",
    "keywords": "wedding gift calculator, how much money to give for a wedding gift, wedding gift amount, cash wedding gift etiquette, how much to spend on a wedding gift",
    "og_title": "Free Wedding Gift Calculator — A Range, Not a Rule",
    "category": "FinanceApplication",
    "h1": "Wedding Gift Calculator",
    "lede": "For guests, not couples. Pick your relationship and circumstances for a cash-gift range grounded in published US etiquette guidance.",
    "panel_title": "Your situation",
    "result_title": "A sensible range",
    "mode": "calc",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-relation">Relationship to the couple</label><select class="ft-select" id="ft-relation" data-ft="relation"><option value="100">Coworker / acquaintance</option><option value="150" selected>Friend or extended family</option><option value="200">Close friend or close relative</option><option value="275">Immediate family / wedding party</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-attend">Attendance</label><select class="ft-select" id="ft-attend" data-ft="attend"><option value="1" selected>Attending alone</option><option value="1.75">Attending with a plus-one</option><option value="0.7">Not attending, sending a gift</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-travel">Travel cost</label><select class="ft-select" id="ft-travel" data-ft="travel"><option value="1" selected>Local, no hotel</option><option value="0.9">Overnight / short drive</option><option value="0.8">Flight + hotel</option><option value="0.7">Destination wedding, significant cost</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-plate">Estimated cost per head (optional)</label><input class="ft-input" type="number" min="0" max="1000" value="110" data-ft="plate" data-ft-default="110"></div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="preevents"> Already gave at a shower or engagement party</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="budget"> My budget is tight right now</label>""",
    "article": """
        <h2>The question every US wedding guest googles</h2>
        <p>The Knot's guest study puts the <strong>average US wedding gift at about $150</strong>, with roughly half of guests giving a physical gift, 40% cash and 10% a gift card. Etiquette pages that rank for this query publish near-identical bands by relationship — which is what the calculator above uses as its starting point.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Relationship</th><th>Widely cited range</th></tr></thead>
            <tbody>
                <tr><td>Coworker, neighbour, acquaintance</td><td>$50–$75 (up to $150 in some guides)</td></tr>
                <tr><td>Friend or extended family</td><td>$75–$125</td></tr>
                <tr><td>Good friend / close relative</td><td>$100–$200</td></tr>
                <tr><td>Immediate family / wedding party</td><td>$200–$300</td></tr>
            </tbody>
        </table></div>
        <h2>What actually changes the number</h2>
        <p>Ranked calculators (ToolAspect, MoneyDeck, Wedding Card Boxes) apply the same handful of adjustments: a plus-one adds roughly $50 because the couple is feeding two of you; a destination wedding lowers the range by about $40 because your flights and hotel are already part of your generosity; not attending cuts it by roughly 30%; and gifts already given at a shower count toward the total. Your budget is the only figure that really matters — no etiquette guide says anyone should go into debt over a gift.</p>
        <h2>The "cover your plate" rule is obsolete</h2>
        <p>The old rule said your gift should equal the cost of your meal. Most modern etiquette writers now reject it: a gift is a token of celebration, not a transaction. It is still useful as a sanity check — The Knot's 2026 Real Weddings Study puts the average US wedding at about $34,200 for 117 guests, roughly $292 per guest all-in, with catering around $80 a head — but no one is auditing your envelope.</p>
        <h2>Cash, cheque, registry or fund?</h2>
        <p>Cash is simplest for the couple; a cheque is safer if the card box is unattended; gift cards and honeymoon funds suit couples who have said what they want. Put the gift in a card with both your names and leave it at the card box rather than handing it to a busy couple. If you are the couple reading this, the <a href="/tools/wedding-thank-you-note-generator/">thank-you note generator</a> is the other end of this exact process.</p>
    """,
    "faq": [
        ("How much should I give as a wedding gift in 2026?", "The Knot's guest study puts the US average at about $150. Widely cited bands run $50–$75 for a coworker, $75–$125 for a friend, $125–$200 for a close friend or relative, and $200–$300 for immediate family or the wedding party."),
        ("Is the cover-your-plate rule still a thing?", "Most etiquette writers now consider it obsolete. A gift is a celebration, not payment for a meal. It can still be a useful floor — catering averages around $80 a head — but your budget and your relationship matter more."),
        ("Do I give more if I bring a plus-one?", "Usually a single joint gift, larger than a solo gift but not double. Ranked calculators add roughly $50 to each end of the range for a plus-one, since the couple is hosting two people."),
        ("Should I give less for a destination wedding?", "Yes, and couples expect it. Etiquette guidance broadly agrees that heavy travel and hotel costs count toward your generosity; the calculator reduces the range accordingly."),
        ("Do I have to give a gift if I cannot attend?", "Not always. A card alone is acceptable for a distant acquaintance, and many guides suggest scaling a gift down by about 30% if you do send one. Close family and friends usually still send something."),
        ("Should I give cash or a physical gift?", "Both are normal. In The Knot's guest study about half gave a physical gift, 40% cash and 10% a gift card. Follow the registry or honeymoon fund if the couple has shared one."),
    ],
    "cta_title": "Here for the couple? Make it a film.",
    "cta_text": "If you are planning rather than attending, turn the day's photos into a cinematic wedding film.",
    "logic": r"""
window.FT_COMPUTE = function (v) {
  var base = parseFloat(v.relation) || 100;
  var attend = parseFloat(v.attend) || 1;
  var travel = parseFloat(v.travel) || 1;
  var amount = base * attend * travel;
  if (v.preevents) amount *= 0.9;
  if (v.budget) amount *= 0.75;
  amount = Math.max(20, Math.round(amount / 5) * 5);
  var low = Math.max(20, Math.round(amount * 0.8 / 5) * 5);
  var high = Math.round(amount * 1.2 / 5) * 5;
  var plate = v.plate || 0;
  var floorNote = plate > 0 ? (amount >= plate ? 'Above the estimated plate cost.' : 'Below the estimated plate cost — fine if the budget is tight.') : '';
  var rows = [
    ['Suggested gift', '$' + amount, 'A single figure to stop second-guessing'],
    ['Comfortable range', '$' + low + ' – $' + high, 'Either end is gracious'],
    ['US average (The Knot guest study)', '$150', 'Reference point only'],
    ['Estimated plate cost per head', plate ? '$' + plate : 'Not set', floorNote || 'Optional sanity check']
  ];
  var lines = ['Wedding gift estimate', 'Suggested: $' + amount + ' (comfortable range $' + low + ' – $' + high + ')', '',
    'Relationship base: $' + base, 'Attendance factor: ' + attend, 'Travel factor: ' + travel,
    v.preevents ? 'Shower / engagement gift already given: -10%' : '',
    v.budget ? 'Tight budget applied: -25%' : ''].filter(Boolean);
  lines.push('', 'A gift is a token of celebration, not a transaction. Give what you can afford gladly.');
  return {
    stats: [
      { num: '$' + amount, lbl: 'Suggested', accent: true },
      { num: '$' + low, lbl: 'Low end' },
      { num: '$' + high, lbl: 'High end' },
      { num: '$150', lbl: 'US average' }
    ],
    head: ['Line', 'Amount', 'Note'], rows: rows,
    note: 'Based on widely cited US etiquette bands and The Knot guest study averages. These are suggestions, not rules — cultural and family traditions come first, and nobody should go into debt over a gift.',
    text: lines.join('\n')
  };
};
""",
})

EXTRA_TOOLS.append({
    "slug": "name-change-checklist",
    "name": "After-Marriage Name Change Checklist",
    "short": "Name Change Checklist",
    "title": "Name Change Checklist After Marriage: The Right Order (Free)",
    "description": "Free interactive name change checklist after marriage. SSA first, then DMV, passport, bank, employer and more — in the order US agencies require. Browser-side, no signup.",
    "keywords": "name change checklist after marriage, change name after wedding, social security name change, passport name change after marriage, newlywed name change order",
    "og_title": "Free Name Change Checklist After Marriage — In Order",
    "category": "ProductivityApplication",
    "h1": "After-Marriage Name Change Checklist",
    "lede": "The order matters. Each US agency checks the one before it — start at Social Security or you get sent home to begin again.",
    "panel_title": "Your details",
    "result_title": "Your checklist",
    "mode": "checklist",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-state">Your state</label><input class="ft-input" type="text" value="California" data-ft="state" data-ft-default="California" placeholder="State"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-when">Marriage date (optional)</label><input class="ft-input" type="date" data-ft="when"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-plan">What you are changing</label><select class="ft-select" id="ft-plan" data-ft="plan"><option value="full">Taking my partner's surname</option><option value="hyphen">Hyphenating</option><option value="keep">Keeping my name (skip most steps)</option></select></div>
                    <p class="ft-hint">This is the federal US sequence. State DMV rules, REAL ID document chains and fees vary — check your state's official site before your appointment.</p>""",
    "article": """
        <h2>Why the sequence is the whole trick</h2>
        <p>USA.gov, the State Department's passport pages and the ranked name-change guides all describe the same dependency chain: <strong>the Social Security Administration's record is what every other agency verifies against</strong>. Update your driver's license before SSA has your new name and the records will not match; the passport application then wants the name already on file. Do it out of order and you repeat the appointment.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Step</th><th>Where</th><th>What to know</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>County / state vital records</td><td>Order 2–3 certified copies of the marriage certificate; several offices keep one</td></tr>
                <tr><td>2</td><td>Social Security (Form SS-5)</td><td>Free; new card in roughly 10–14 business days, same number, new name</td></tr>
                <tr><td>3</td><td>State DMV / ID office</td><td>In person in most states; many require the 30-day window after marriage</td></tr>
                <tr><td>4</td><td>U.S. passport (State Dept)</td><td>Form depends on how recently the passport was issued — DS-5504, DS-82 or DS-11</td></tr>
                <tr><td>5</td><td>Banks, cards, loans</td><td>Bring the new ID and a certified certificate</td></tr>
                <tr><td>6</td><td>Employer / payroll</td><td>HR updates tax records, direct deposit, insurance and work email</td></tr>
                <tr><td>7</td><td>Voter registration</td><td>vote.gov routes you to your state's process</td></tr>
                <tr><td>8</td><td>Everything else</td><td>Insurance, utilities, subscriptions, loyalty accounts, medical records</td></tr>
            </tbody>
        </table></div>
        <h2>Documents worth gathering up front</h2>
        <ul>
            <li>Certified marriage certificates (2–3 copies — photocopies are not accepted)</li>
            <li>Current driver's license or state ID, plus birth certificate for a REAL ID chain</li>
            <li>Current passport and a new passport photo</li>
            <li>Form SS-5, and the correct passport form for your situation</li>
        </ul>
        <p>The State Department notes that if you can show an ID already issued in your new name, you may not need to submit separate proof of the name change with the passport application — but the DS-11 still asks for the marriage details. Rules differ by state and by how long ago your passport was issued, so treat this list as an organiser, not legal advice.</p>
        <h2>Not changing your name?</h2>
        <p>That is now common and requires none of this. Select "Keeping my name" and the checklist narrows to the practical updates: travel bookings, emergency contacts, and making sure your passport and ticket names match exactly. Either way, the other post-wedding task with a deadline is <a href="/tools/wedding-thank-you-note-generator/">thank-you cards</a>, which US etiquette targets at 4–6 weeks.</p>
    """,
    "faq": [
        ("What do I change first after getting married?", "The Social Security record, immediately after you have certified copies of your marriage certificate. Every other agency — DMV, passport office, banks, employers — verifies your name against SSA's database."),
        ("How many certified marriage certificates do I need?", "Two to three. Several agencies want their own certified copy and some will not return it. Photocopies and notarised copies are not accepted for the SSA or passport application."),
        ("How long does the Social Security name change take?", "The new card typically arrives in about 10–14 business days. It carries the same number with your new name, and there is no fee."),
        ("Which passport form do I use?", "It depends on timing: DS-5504 if the passport was issued less than a year ago and the name changed within that year; DS-82 for a standard renewal by mail; DS-11 if you must apply in person. Check travel.state.gov before sending anything."),
        ("Do I have to change my name after marriage?", "No. Keeping your birth name is common and requires no government filings. If you travel, just make sure the name on the ticket matches the passport exactly."),
        ("Is my checklist progress private?", "Yes. Tick states are stored only in this browser's local storage on this device. Nothing is uploaded and there is no account or email capture."),
    ],
    "logic": r"""
window.FT_GROUPS = [
  { title: 'Step 1 — Documents (do this first)', items: [
    { id: 'n1', text: 'Order 2–3 certified copies of the marriage certificate' },
    { id: 'n2', text: 'Gather current photo ID, birth certificate and Social Security card' },
    { id: 'n3', text: 'Get a new passport photo' },
    { id: 'n4', text: 'Check your state DMV name-change window (often 30 days)' }
  ]},
  { title: 'Step 2 — Social Security (Form SS-5)', items: [
    { id: 'n5', text: 'Complete Form SS-5 with your new legal name' },
    { id: 'n6', text: 'Submit with a certified marriage certificate and proof of identity' },
    { id: 'n7', text: 'Wait ~10–14 business days for the new card (same number)' }
  ]},
  { title: 'Step 3 — Driver license / state ID', items: [
    { id: 'n8', text: 'Book the DMV appointment for your state' },
    { id: 'n9', text: 'Bring the new Social Security record, current license and certificate' },
    { id: 'n10', text: 'For REAL ID, bring documents linking every prior name change' }
  ]},
  { title: 'Step 4 — U.S. passport', items: [
    { id: 'n11', text: 'Pick the form: DS-5504, DS-82 or DS-11 based on issue date' },
    { id: 'n12', text: 'Mail / apply with the certificate, photo and current passport' },
    { id: 'n13', text: 'Wait for the new passport before booking travel in the new name' }
  ]},
  { title: 'Step 5 — Money and work', items: [
    { id: 'n14', text: 'Update checking, savings, credit cards and loans' },
    { id: 'n15', text: 'Tell payroll / HR so the W-2 and direct deposit match SSA' },
    { id: 'n16', text: 'Update insurance beneficiaries, investments and tax records' }
  ]},
  { title: 'Step 6 — The long tail', items: [
    { id: 'n17', text: 'Voter registration (vote.gov routes to your state)' },
    { id: 'n18', text: 'USPS, utilities, phone and internet accounts' },
    { id: 'n19', text: 'Medical records, prescriptions and pharmacy' },
    { id: 'n20', text: 'Subscriptions, loyalty programs and frequent-flyer accounts' },
    { id: 'n21', text: 'Email signature, social profiles and professional listings' },
    { id: 'n22', text: 'Send thank-you cards while the list is still fresh' }
  ]}
];
window.FT_INIT = function (api) {
  var wrap = api.$('#ft-progress-wrap');
  if (wrap) wrap.style.display = '';
  var plan = api.$('[data-ft="plan"]');
  function apply() {
    var note = api.$('#ft-note');
    if (!note) return;
    if (!plan || plan.value !== 'keep') {
      note.style.display = '';
      note.textContent = 'Order matters: SSA first, then DMV, then passport. Each agency checks the one before it. Check your state DMV and travel.state.gov for the exact forms.';
    } else {
      note.style.display = '';
      note.textContent = 'Keeping your name? No government filings are needed. Just make sure travel bookings match your passport exactly.';
    }
  }
  if (plan) plan.addEventListener('change', apply);
  apply();
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-thank-you-note-generator",
    "name": "Wedding Thank-You Note Generator",
    "short": "Thank-You Notes",
    "title": "Wedding Thank-You Note Generator: Every Guest, Free",
    "description": "Free wedding thank-you card wording generator. Pick the gift type and tone, get a warm ready-to-copy note, and batch your whole gift list. No signup, browser-side.",
    "keywords": "wedding thank you card wording, thank you note generator, what to write in wedding thank you cards, thank you for cash gift wording, wedding thank you message examples",
    "og_title": "Free Wedding Thank-You Note Generator — One Note Per Guest",
    "category": "WritingApplication",
    "h1": "Wedding Thank-You Note Generator",
    "lede": "One note is easy. A hundred and forty — each different enough that two cousins comparing cards do not find the same sentence — is the actual task.",
    "panel_title": "Your note",
    "result_title": "Ready to copy",
    "mode": "generator",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-guest">Guest name(s)</label><input class="ft-input" type="text" value="Aunt Susan and Uncle Tom" data-ft="guest" data-ft-default="Aunt Susan and Uncle Tom"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-gift">What they gave</label><select class="ft-select" id="ft-gift" data-ft="gift"><option value="registry">A registry gift</option><option value="cash">Cash or a cheque</option><option value="group">A group gift</option><option value="nogift">No gift — they attended</option><option value="travel">They travelled a long way</option><option value="absent">They could not attend</option><option value="vendor">A vendor or helper</option><option value="party">Wedding party member</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-item">What it was / what it is for (optional)</label><input class="ft-input" type="text" value="our first home" data-ft="item" data-ft-default="our first home" placeholder="the stand mixer / our honeymoon"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-tone">Tone</label><select class="ft-select" id="ft-tone" data-ft="tone"><option value="warm">Warm</option><option value="formal">Formal</option><option value="short">Short</option><option value="playful">Playful</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-sign">Signed from</label><input class="ft-input" type="text" value="Sarah and Michael" data-ft="sign" data-ft-default="Sarah and Michael"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-batch">Batch mode — one guest per line (optional)</label><textarea class="ft-textarea" data-ft="batch" placeholder="Aunt Susan | a cheque | the deposit on our house&#10;Priya | honeymoon fund | our first dinner out"></textarea></div>
                    <p class="ft-hint">Never name the amount of a cash gift. US etiquette targets 4–6 weeks after the wedding; three months is the outer limit most guests notice.</p>""",
    "article": """
        <h2>The post-wedding task nobody budgets time for</h2>
        <p>Zola's free Instant Thank Yous, TheWeddingPlanner.ai and Text My Wedding all exist for the same reason: a 100-guest wedding means <strong>100+ individually worded notes</strong>. The ranked tools converge on the same recipe — greet by name, name the specific gift, say how you will use it, add one personal memory, close warmly, and send within 4–6 weeks.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Situation</th><th>What the note must do</th></tr></thead>
            <tbody>
                <tr><td>Registry gift</td><td>Name the item and say how it is already being used</td></tr>
                <tr><td>Cash or cheque</td><td>Thank the generosity, never the amount; name what it is going toward</td></tr>
                <tr><td>Group gift</td><td>Thank each contributor individually, and mention the group</td></tr>
                <tr><td>No gift, but attended</td><td>Focus entirely on their presence; never mention the absence of a gift</td></tr>
                <tr><td>Could not attend</td><td>Say they were missed; a card alone is fine for distant acquaintances</td></tr>
                <tr><td>Destination traveller</td><td>Acknowledge the journey specifically — it was a real cost and effort</td></tr>
                <tr><td>Vendor / wedding party</td><td>Formal tone, name the specific help, no sales language</td></tr>
            </tbody>
        </table></div>
        <h2>Batch mode, and why the notes must differ</h2>
        <p>Paste one guest per line as <code>Name | gift | what it is for</code> and the tool writes a different note for each row — the detail ranked tools call out as the difference between 140 notes and one note printed 140 times. Two cousins comparing cards at Thanksgiving should not find identical sentences.</p>
        <h2>Handwritten, typed or sent by message?</h2>
        <p>Zola notes that digital thank-you notes are now widely accepted, and Australian/US guides agree a warm message beats a late formal card. A short, timely note always reads better than a long, late one. If you are writing by hand, use Print / PDF for the drafts and keep them at the kitchen table with a pen.</p>
        <p>Once the notes are done, the other post-wedding job with an order dependency is the <a href="/tools/name-change-checklist/">name change sequence</a>. And the guest list you just worked through is the same list that feeds a <a href="/blog/wedding-video-from-photos/">wedding film</a> share — the moment most couples finally send it out.</p>
    """,
    "faq": [
        ("How soon should wedding thank-you cards be sent?", "US and Australian etiquette guidance targets four to six weeks after the wedding; three months is the outer limit most guests notice. A short, timely note always reads better than a long, late one."),
        ("What do I write for a cash gift?", "Thank the generosity without naming the amount, then say what it is going toward — the honeymoon, a first home, or savings. A specific purpose turns a polite line into a warm one."),
        ("Do I have to send a note to someone who did not give a gift?", "Yes if they attended. Focus entirely on their presence and a shared memory from the day, and never mention that no gift was received."),
        ("Can I send thank-you notes by email or message?", "Yes. Zola and other ranked guides say digital notes are now widely accepted, especially for close friends. Handwritten cards still carry more weight for older relatives and formal families."),
        ("How do I stop 140 notes sounding identical?", "Use batch mode: one guest per line with their own gift and purpose, and each note is written from its own inputs. Vary the tone between warm, formal, short and playful for different groups."),
        ("Is anything I type uploaded?", "No. Names, gifts and notes stay in this browser. There is no account, no server call and no AI model — the wording is assembled from templates you control."),
    ],
    "cta_title": "Send the film with the thanks.",
    "cta_text": "Most couples share their wedding film in the same week as the thank-you notes. Make yours from the photos you already have.",
    "logic": r"""
window.FT_GENERATE = function (v, variant) {
  function one(guest, gift, item) {
    guest = (guest || '').trim() || 'Dear friend';
    item = (item || '').trim() || 'our first year together';
    gift = gift || 'registry';
    var tone = v.tone || 'warm';
    var sign = (v.sign || '').trim() || 'The two of us';
    var body = {
      registry: 'Thank you so much for the ' + item + '. It is already part of our everyday, and we think of you every time we use it.',
      cash: 'Thank you for your incredibly generous gift. We are putting it toward ' + item + ', and it means more than we can say.',
      group: 'Thank you for being part of the group gift — the ' + item + ' is exactly what we needed, and we are grateful to each of you.',
      nogift: 'Thank you for celebrating with us. Having you in the room made the day feel complete, and we are still smiling about it.',
      travel: 'We still cannot believe you travelled all that way to be there. It meant everything to have you with us.',
      absent: 'We missed you on the day, but you were very much in our thoughts. Knowing you were cheering us on from afar meant a lot.',
      vendor: 'Thank you for the care and skill you brought to our wedding. The day ran as it did because of your work.',
      party: 'Thank you for standing beside us — and for everything you did in the months before. We would not have got here so calmly without you.'
    }[gift];
    var open = {
      warm: 'Dear ' + guest + ',', formal: 'Dear ' + guest + ',',
      short: 'Dear ' + guest + ',', playful: 'Dear ' + guest + ','
    }[tone];
    var memory = {
      warm: 'It was wonderful to see you on the dance floor, and we are so glad you were part of it.',
      formal: 'We are grateful you could join us and share in the celebration.',
      short: 'With thanks for being there.',
      playful: 'We hope you recovered from the dance floor as quickly as we did.'
    }[tone];
    var close = {
      warm: 'With love,', formal: 'With gratitude,', short: 'Love,', playful: 'All our love,'
    }[tone];
    if (tone === 'short') return [open, body, close, sign].join('\n');
    return [open, body, memory, close, sign].join('\n');
  }
  var batch = (v.batch || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  var blocks = [];
  if (batch.length) {
    batch.forEach(function (line, i) {
      var parts = line.split('|').map(function (s) { return s.trim(); });
      var giftGuess = v.gift || 'registry';
      if (/cheque|check|cash|money/i.test(parts[1] || '')) giftGuess = 'cash';
      else if (/honeymoon|fund/i.test(parts[1] || '')) giftGuess = 'cash';
      blocks.push({ title: 'Note ' + (i + 1) + ' — ' + parts[0], text: one(parts[0], giftGuess, parts[2] || parts[1] || v.item) });
    });
  } else {
    blocks.push({ title: 'Your thank-you note', text: one(v.guest, v.gift, v.item) });
  }
  var all = blocks.map(function (b) { return b.text; }).join('\n\n---\n\n');
  var words = all.trim().split(/\s+/).length;
  return {
    blocks: blocks,
    stats: [
      { num: blocks.length, lbl: 'Notes', accent: true },
      { num: words, lbl: 'Words total' },
      { num: '4–6', lbl: 'Weeks to send' }
    ],
    note: batch.length ? 'Batch of ' + blocks.length + ' notes. Read each one before copying to a card — add one real detail from the day where you can.' : 'Never name the amount of a cash gift. Add one specific memory from the day if you have one, and send within 4–6 weeks.',
    text: all
  };
};
window.FT_INIT = function () {
  var again = document.getElementById('ft-again');
  if (again) { again.style.display = 'none'; again.textContent = 'Try another phrasing'; }
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-cake-serving-calculator",
    "name": "Wedding Cake Serving Calculator",
    "short": "Cake Calculator",
    "title": "Wedding Cake Serving Calculator: Tiers & Sizes (Free)",
    "description": "Free wedding cake calculator. Enter your guest count for a tier recommendation and exact servings for round or square cakes, US dessert and UK finger portions.",
    "keywords": "wedding cake serving calculator, wedding cake size calculator, how many tiers for 100 guests, cake servings chart, wedding cake portion guide",
    "og_title": "Free Wedding Cake Calculator — Tiers, Sizes, Servings",
    "category": "FinanceApplication",
    "h1": "Wedding Cake Serving Calculator",
    "lede": "How many tiers, and what size? The industry standard is a 1×2 inch slice — this converts your guest count into an actual tier plan.",
    "panel_title": "Your cake",
    "result_title": "Recommended tiers",
    "mode": "calc",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-guests">Guests to serve</label><input class="ft-input" type="number" min="1" max="1000" value="100" data-ft="guests" data-ft-default="100"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-shape">Cake shape</label><select class="ft-select" id="ft-shape" data-ft="shape"><option value="round">Round tiers</option><option value="square">Square tiers (25–35% more servings)</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-portion">Portion style</label><select class="ft-select" id="ft-portion" data-ft="portion"><option value="dessert">US dessert portion (1×2 in)</option><option value="finger">UK finger portion (1×1 in)</option><option value="generous">Generous slices (2×2 in)</option></select></div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="top" checked> Save the top tier for our first anniversary</label>
                    <label class="ft-checkline"><input type="checkbox" data-ft="buffer" checked> Add a 10% buffer for seconds</label>""",
    "article": """
        <h2>The slice that decides everything</h2>
        <p>Every ranked cake calculator — Plana, WeddingCakesHub, WedCalc — uses the same industry standard: a <strong>1 inch × 2 inch × 4 inch wedge</strong>, roughly the width of two fingers. In the US that is the "dessert portion" served as the main dessert. In the UK the standard is a smaller "finger portion" (1×1 in), which yields about 35% more slices from the same cake. Choose the right one before you order.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Round tier</th><th>US dessert portions</th><th>UK finger portions</th><th>Generous (2×2 in)</th></tr></thead>
            <tbody>
                <tr><td>6 in</td><td>12</td><td>18</td><td>8</td></tr>
                <tr><td>8 in</td><td>24</td><td>24</td><td>16</td></tr>
                <tr><td>10 in</td><td>38</td><td>38</td><td>25</td></tr>
                <tr><td>12 in</td><td>56</td><td>54</td><td>36</td></tr>
                <tr><td>14 in</td><td>78</td><td>72</td><td>50</td></tr>
                <tr><td>16 in</td><td>100</td><td>—</td><td>66</td></tr>
            </tbody>
        </table></div>
        <p>Square tiers yield roughly 25–35% more servings than rounds of the same diameter, because there are no curved edges to trim. Bakers rarely go above a 16-inch base tier for structural reasons; for more than 200 guests the standard solution is a display cake plus sheet cake cut in the kitchen.</p>
        <h2>Worked examples</h2>
        <p><strong>100 guests:</strong> the classic 3-tier round 12 / 9 / 6 inch combination serves about 100 dessert portions. <strong>150 guests:</strong> a 4-tier 14 / 10 / 8 / 6 inch stack serves about 152. With finger portions a 3-tier 12 / 9 / 6 can stretch to 150.</p>
        <h2>Two traditions that change the math</h2>
        <p>If you are saving the top tier for your first anniversary — a long-standing UK tradition that has spread to US weddings — add 10–15% to the guest count or order a small separate kitchen cake for that tier's servings. And always tell your baker the portion style you planned around: a generous cut can turn a 3-tier job into a 4-tier one.</p>
        <p>Cake is only one dessert line. For the bar, use the <a href="/tools/wedding-alcohol-calculator/">alcohol calculator</a>; for the headcount behind both, the <a href="/tools/wedding-guest-count-calculator/">guest count calculator</a>.</p>
    """,
    "faq": [
        ("How many tiers do I need for 100 wedding guests?", "For US dessert-size portions, a classic 3-tier round cake of 12, 9 and 6 inches serves about 100. With smaller UK finger portions, a 2-tier 10/6 cake can cover 100 guests."),
        ("What size wedding cake do I need for 150 guests?", "A 4-tier round 14 / 10 / 8 / 6 inch combination serves about 152 dessert portions. With finger portions, a 3-tier 12 / 9 / 6 stack will usually cover 150."),
        ("What is the difference between dessert and finger portions?", "A US dessert portion is about 1×2 inches and is served as the main dessert. A UK finger portion is roughly 1×1 inch — about 30% smaller — so the same cake yields about 35% more slices. It suits weddings where cake follows a dessert course."),
        ("Do square cakes serve more people?", "Yes, around 25–35% more than a round tier of the same diameter, because every inch can be cut into neat rectangular slices. An 8-inch square gives about 32 finger portions versus 24 for a round."),
        ("Should I count the top tier if I am saving it?", "No. Exclude its servings from the guest total and add 10–15% to your count, or order a small kitchen cake to supplement. Freezing the top tier for the first anniversary works best with a dense fruit cake."),
        ("Can one display cake feed 250 guests?", "Not elegantly. Bakers rarely exceed a 16-inch base tier. The standard approach for large weddings is a beautiful 3- or 4-tier display cake plus sheet cake cut in the kitchen and served as slices."),
    ],
    "logic": r"""
window.FT_COMPUTE = function (v) {
  var guests = Math.max(1, v.guests || 1);
  var target = guests * (v.buffer ? 1.10 : 1);
  var round = { 6: 12, 8: 24, 9: 32, 10: 38, 12: 56, 14: 78, 16: 100 };
  var finger = { 6: 18, 8: 24, 9: 30, 10: 38, 12: 54, 14: 72, 16: 96 };
  var generous = { 6: 8, 8: 16, 9: 21, 10: 25, 12: 36, 14: 50, 16: 66 };
  var table = v.portion === 'finger' ? finger : v.portion === 'generous' ? generous : round;
  var factor = v.shape === 'square' ? 1.3 : 1;
  function servings(size) { return Math.round(table[size] * factor); }
  var combos = [[12,9,6],[10,6],[8,6],[14,10,8,6],[16,12,10,8,6],[14,12,10,8],[12,10,8,6],[16,12,8]];
  var best = null;
  combos.forEach(function (c) {
    var available = c.slice().sort(function (a,b) { return b-a; });
    var use = v.top ? available.slice(1) : available;
    var total = use.reduce(function (s, size) { return s + servings(size); }, 0);
    var diff = total - target;
    if (total >= target && (!best || diff < best.diff || (diff === best.diff && use.length < best.use.length))) {
      best = { sizes: available, use: use, total: total, diff: diff };
    }
  });
  if (!best) best = { sizes: [16,12,10,8,6], use: [16,12,10,8,6], total: 100, diff: 0 };
  var rows = best.sizes.map(function (size) {
    var saved = v.top && size === Math.min.apply(null, best.sizes);
    return [size + '" ' + (v.shape === 'square' ? 'square' : 'round'),
            servings(size) + ' servings',
            saved ? 'Saved for the first anniversary' : (v.portion === 'finger' ? 'Finger portions' : v.portion === 'generous' ? 'Generous slices' : 'Dessert portions')];
  });
  rows.push(['Total available to guests', best.total + ' servings', 'Target ' + Math.ceil(target) + ' including buffer']);
  var lines = ['Wedding cake plan for ' + guests + ' guests', 'Tiers: ' + best.sizes.join('" / ') + '"', ''];
  rows.forEach(function (r) { lines.push(r[0] + ': ' + r[1] + ' — ' + r[2]); });
  lines.push('', 'Confirm the portion style with your baker. For 200+ guests consider a display cake plus kitchen sheet cake.');
  return {
    stats: [
      { num: best.sizes.length, lbl: 'Tiers', accent: true },
      { num: best.total, lbl: 'Servings' },
      { num: Math.ceil(target), lbl: 'Guests + buffer' },
      { num: best.diff, lbl: 'Spare slices' }
    ],
    head: ['Tier', 'Servings', 'Note'], rows: rows,
    note: v.top ? 'The smallest tier is excluded from the guest count for the anniversary tradition. Add 10–15% if you want a buffer on top of that.' : 'Standard US 1×2 in dessert portions. Tell your baker which portion style you planned around before confirming the order.',
    text: lines.join('\n')
  };
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-dress-code-decoder",
    "name": "Wedding Dress Code Decoder",
    "short": "Dress Code Decoder",
    "title": "Wedding Guest Dress Code Decoder: What Every Label Means",
    "description": "Free wedding dress code decoder. Pick the wording on the invitation for exactly what to wear — black tie, cocktail, semi-formal, beach, festive — for men and women.",
    "keywords": "wedding dress code decoder, what does black tie optional mean, cocktail attire wedding guest, semi formal wedding attire, what to wear to a wedding",
    "og_title": "Free Wedding Dress Code Decoder — Every Invite Wording",
    "category": "ReferenceApplication",
    "h1": "Wedding Guest Dress Code Decoder",
    "lede": '"Black tie optional" has ruined more guest outfits than rain has ruined ceremonies. Pick the wording on the invite and get a straight answer.',
    "panel_title": "On the invitation",
    "result_title": "What it means",
    "mode": "calc",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-code">Dress code wording</label><select class="ft-select" id="ft-code" data-ft="code"><option value="white">White tie</option><option value="black">Black tie</option><option value="bto">Black tie optional</option><option value="formal">Formal / formal attire</option><option value="cocktail" selected>Cocktail attire</option><option value="semi">Semi-formal / dressy casual</option><option value="festive">Festive attire</option><option value="beach">Beach / tropical formal</option><option value="garden">Garden party</option><option value="casual">Casual / come as you are</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-time">Time of day</label><select class="ft-select" id="ft-time" data-ft="time"><option value="day">Daytime</option><option value="evening" selected>Evening (after 6pm)</option></select></div>
                    <div class="ft-row"><label class="ft-label" for="ft-venue">Venue</label><select class="ft-select" id="ft-venue" data-ft="venue"><option value="ballroom">Ballroom / hotel / city</option><option value="outdoor" selected>Outdoor / garden / barn</option><option value="beach">Beach / destination</option></select></div>
                    <p class="ft-hint">Vogue, The Knot and Emily Post guidance all place these codes on one formality ladder — once you see the rung, the outfit takes five minutes.</p>""",
    "article": """
        <h2>One ladder, ten labels</h2>
        <p>Vogue's guide to modern guest dress codes and the ranked US etiquette pages all describe the same spectrum, from white tie down to casual. The confusion comes from invented labels — "Romantic Garden Attire", "Elevated Casual", "Champagne Dreams" — which couples increasingly print on invitations. Emily Post's guidance is to map the invented phrase to the nearest standard rung, then calibrate for venue and time of day.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Code</th><th>Women</th><th>Men</th></tr></thead>
            <tbody>
                <tr><td>White tie</td><td>Full-length ball gown</td><td>Tailcoat, white bow tie, waistcoat</td></tr>
                <tr><td>Black tie</td><td>Floor-length gown or elegant pantsuit</td><td>Tuxedo, black bow tie</td></tr>
                <tr><td>Black tie optional</td><td>Long gown or elevated cocktail dress</td><td>Tuxedo or dark formal suit, tie required</td></tr>
                <tr><td>Formal</td><td>Long dress or dressy midi</td><td>Dark suit and tie</td></tr>
                <tr><td>Cocktail</td><td>Knee-to-midi dress, dressy jumpsuit</td><td>Suit, tie optional in summer</td></tr>
                <tr><td>Semi-formal</td><td>Dressy separates or a polished dress</td><td>Blazer, dress shirt, tie optional</td></tr>
                <tr><td>Festive</td><td>Bold colour, pattern, velvet</td><td>Suit with personality</td></tr>
                <tr><td>Beach / garden</td><td>Flowy midi or maxi, wedges or block heels</td><td>Light linen suit, no tie, loafers</td></tr>
                <tr><td>Casual</td><td>Sundress or refined separates</td><td>Chinos and a collared shirt</td></tr>
            </tbody>
        </table></div>
        <h2>The rules that still hold in 2026</h2>
        <p><strong>No white, ivory, cream or champagne</strong> — that remains the firmest rule in Western wedding etiquette, including "but it has tiny flowers on it". Avoid the bridal party's exact colour if you know it. <strong>Black is now fully acceptable</strong> at modern US and European weddings; the old mourning association has largely faded, though some families and faith communities still hold it. And "casual" at a wedding is still three levels above a couch outfit — jeans and sneakers only if the invitation literally says so.</p>
        <h2>Three calibration rules</h2>
        <ul>
            <li><strong>Ceremony trumps reception.</strong> Dress for the most formal part of the day; you can shed a jacket later.</li>
            <li><strong>Venue is a hint.</strong> Ballroom means go up a rung; barn or beach means down — unless the invite says otherwise.</li>
            <li><strong>When in doubt, overdress slightly.</strong> Slightly overdressed always photographs better, and a 20-second text to the couple beats an evening of feeling wrong.</li>
        </ul>
        <p>If you are the couple writing that line on the invitation, put the standard wording bottom-right on the invite or on your wedding website — one line saves fifty texts. For the wording itself, see the <a href="/tools/wedding-invitation-maker/">invitation maker</a>.</p>
    """,
    "faq": [
        ("What does black tie optional actually mean?", "The couple wants a black-tie look but will not force you to rent a tux. Men: a tuxedo if you own one, otherwise your darkest suit with a conservative tie. Women: a long gown, a formal midi or dressy separates. 'Optional' applies to the tux, not to dressing formally."),
        ("Can I wear black to a wedding?", "Yes. Black is fully accepted at modern US and European weddings, especially cocktail and black-tie ones. Avoid it only at explicitly bright or festive daytime weddings, or add colour through accessories. Some families and faith communities still associate it with mourning."),
        ("What should a wedding guest never wear?", "White, ivory, cream or anything close to it; the bridal party's exact colour; jeans and sneakers unless the invitation says casual; and anything attention-grabbing enough to pull focus from the couple."),
        ("What is the difference between formal, semi-formal and cocktail?", "Formal sits near black-tie optional (dark suit, long or dressy midi dress). Cocktail is the most common US code (suit, knee-to-midi dress). Semi-formal is one rung down (blazer, dressy separates). When unsure, take the higher rung."),
        ("What should I wear to a beach or garden wedding?", "Light fabrics — linen, chiffon, cotton. Women: a flowy midi or maxi with wedges or block heels (stilettos sink into grass and sand). Men: a light suit or blazer with an open collar, no tie, loafers."),
        ("What if the invitation uses an invented dress code?", "Map the phrase to the nearest standard rung: 'Romantic Garden Attire' is garden-party semi-formal; 'Festive and Fun' is cocktail with colour. Then check the wedding website for a 'What to Wear' note and calibrate for venue and start time."),
    ],
    "cta_title": "Dressed up? Get it on film.",
    "cta_text": "The outfits, the vows, the dance floor — keep them in a cinematic wedding film made from your photos.",
    "logic": r"""
window.FT_COMPUTE = function (v) {
  var codes = {
    white: { rank: 1, name: 'White tie', women: 'Full-length formal ball gown, fine jewellery, an evening clutch', men: 'Black tailcoat, white waistcoat, white bow tie, patent leather shoes', avoid: 'Anything shorter than floor length; a black tie in place of a white one' },
    black: { rank: 2, name: 'Black tie', women: 'Floor-length gown or an elegant tailored pantsuit in silk, velvet or lace', men: 'Black or midnight-navy tuxedo, white dress shirt, black bow tie, polished black shoes', avoid: 'Midi dresses, casual fabrics, open-toed shoes with a tux' },
    bto: { rank: 3, name: 'Black tie optional', women: 'Long gown, elevated cocktail dress or a formal jumpsuit — you cannot overdress here', men: 'Tuxedo if you own one, otherwise a dark navy/charcoal suit, white shirt, conservative tie', avoid: 'Light-grey suits, short casual dresses, anything laid-back' },
    formal: { rank: 4, name: 'Formal / formal attire', women: 'Long dress or a dressy midi in a refined fabric', men: 'Dark suit and tie', avoid: 'Denim, sundresses, sneakers' },
    cocktail: { rank: 5, name: 'Cocktail attire', women: 'Knee-to-midi dress or a dressy jumpsuit; elegant clutch', men: 'Tailored suit; tie recommended but droppable at a summer daytime wedding', avoid: 'Clubwear, very short hemlines, anything you would wear to a bar' },
    semi: { rank: 6, name: 'Semi-formal / dressy casual', women: 'Dressy dress, skirt set or polished separates', men: 'Blazer or sport coat, dress shirt, tie optional', avoid: 'Jeans — "semi" does not mean casual' },
    festive: { rank: 5, name: 'Festive attire', women: 'Bold colour, pattern, velvet or statement jewellery', men: 'Suit with personality — colour, pattern, a pocket square', avoid: 'Beige neutrality; the couple is asking for effort and fun' },
    beach: { rank: 7, name: 'Beach / tropical formal', women: 'Breezy maxi or midi in linen/chiffon; dressy flat sandals or wedges', men: 'Linen trousers and a light cotton or linen shirt, no tie, loafers or sandals', avoid: 'Stilettos (they sink), heavy wool, flip-flops' },
    garden: { rank: 6, name: 'Garden party', women: 'Floral or pastel midi/maxi, block heels or wedges', men: 'Light suit or blazer, open collar', avoid: 'Stiletto heels on grass; bring a layer for the evening' },
    casual: { rank: 8, name: 'Casual / come as you are', women: 'Sundress, skirt or refined separates', men: 'Chinos or dress pants with a button-down, jacket optional', avoid: 'Ripped jeans, tank tops, athletic wear — casual still means put-together' }
  };
  var c = codes[v.code] || codes.cocktail;
  var rows = [
    ['Formality', c.rank + ' of 10', 'Lower number = more formal'],
    ['Women', c.women, 'Dress for the ceremony, not just the reception'],
    ['Men', c.men, v.time === 'day' ? 'Daytime: lighter fabrics and colours are fine' : 'Evening: darker, richer fabrics'],
    ['Avoid', c.avoid, 'Plus the universal rules below'],
    ['Universal rule 1', 'No white, ivory, cream or champagne', 'Includes pale prints and near-whites'],
    ['Universal rule 2', 'Do not match the bridal party colour', 'Check the wedding website if it is listed'],
    ['Universal rule 3', 'Black is acceptable', 'Add colour with accessories for a daytime wedding'],
    ['Venue calibration', v.venue === 'ballroom' ? 'Ballroom / city — go up one rung' : v.venue === 'beach' ? 'Beach — go down one rung, mind the sand' : 'Outdoor / barn — go down one rung, mind the grass', 'Unless the invitation explicitly overrides it']
  ];
  var lines = ['Dress code: ' + c.name, 'Women: ' + c.women, 'Men: ' + c.men, 'Avoid: ' + c.avoid, '', 'No white / ivory / cream. Black is fine. When in doubt, overdress slightly.'];
  return {
    stats: [
      { num: c.rank, lbl: 'Formality rank', accent: true },
      { num: v.time === 'day' ? 'Day' : 'Eve', lbl: 'Time of day' },
      { num: v.venue === 'ballroom' ? 'Up' : 'Down', lbl: 'Venue adjust' },
      { num: '3', lbl: 'Universal rules' }
    ],
    head: ['Point', 'Guidance', 'Why'], rows: rows,
    note: 'Mapped from the standard ladder published by Vogue, The Knot and Emily Post guidance. For invented labels, pick the nearest rung, then check the couple\'s wedding website — a 20-second text beats an evening of feeling wrong.',
    text: lines.join('\n')
  };
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-vendor-tipping-calculator",
    "name": "Wedding Vendor Tip Calculator",
    "short": "Tip Calculator",
    "title": "Wedding Vendor Tip Calculator: Cash Envelopes, Sorted",
    "description": "Free US wedding vendor tipping calculator. Enter your vendor bills for a suggested tip per envelope and a total cash figure. Handles service-charge contracts. No signup.",
    "keywords": "wedding vendor tipping calculator, how much to tip wedding vendors, wedding tip calculator, do you tip the photographer, wedding caterer tip",
    "og_title": "Free Wedding Vendor Tip Calculator — Envelope by Envelope",
    "category": "FinanceApplication",
    "h1": "Wedding Vendor Tip Calculator",
    "lede": "Nobody invoices you for tips. They are cash, due on the day, and the last thing anyone budgets — this turns your contracts into a labelled envelope list.",
    "panel_title": "Your contracts",
    "result_title": "Cash to set aside",
    "mode": "calc",
    "panel": """                    <div class="ft-row-2"><div class="ft-row"><label class="ft-label" for="ft-food">Food &amp; beverage bill</label><input class="ft-input" type="number" min="0" value="6000" data-ft="food" data-ft-default="6000"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-rate">Catering tip rate (%)</label><input class="ft-input" type="number" min="0" max="30" value="18" data-ft="rate" data-ft-default="18"></div></div>
                    <label class="ft-checkline"><input type="checkbox" data-ft="service"> Contract already distributes its service charge to staff</label>
                    <div class="ft-row-2"><div class="ft-row"><label class="ft-label" for="ft-bar">Bar bill</label><input class="ft-input" type="number" min="0" value="2500" data-ft="bar" data-ft-default="2500"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-hmu">Hair &amp; makeup bill</label><input class="ft-input" type="number" min="0" value="900" data-ft="hmu" data-ft-default="900"></div></div>
                    <div class="ft-row"><label class="ft-label" for="ft-dj">DJ / band flat tip</label><input class="ft-input" type="number" min="0" value="125" data-ft="dj" data-ft-default="125"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-photo">Photographer / videographer flat tip</label><input class="ft-input" type="number" min="0" value="200" data-ft="photo" data-ft-default="200"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-officiant">Officiant honorarium</label><input class="ft-input" type="number" min="0" value="75" data-ft="officiant" data-ft-default="75"></div>
                    <p class="ft-hint">A service charge (often 18–24%) is not automatically a gratuity. Ask the manager whether it reaches the staff before tipping twice.</p>""",
    "article": """
        <h2>The trap that costs couples hundreds</h2>
        <p>Every ranked 2026 tipping guide leads with the same warning: <strong>a "service charge" on a catering or venue contract (often 18–24%) is not necessarily a tip</strong>. It may be a house fee that never reaches the staff. Ask the manager directly whether it is distributed as gratuity. If it is, you are covered; if it is not, tip the servers and bartenders directly. Never pay a separate gratuity line twice.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Vendor</th><th>Customary US tip</th><th>Note</th></tr></thead>
            <tbody>
                <tr><td>Caterer &amp; wait staff</td><td>15–20% of food &amp; beverage</td><td>Only if no distributed service charge</td></tr>
                <tr><td>Bartenders</td><td>10% of the bar bill, or $20–$50 each</td><td>Often built into the bar package</td></tr>
                <tr><td>Hair &amp; makeup</td><td>15–20% of the service bill</td><td>Tip like a salon visit</td></tr>
                <tr><td>DJ</td><td>10–15% or $50–$150 flat</td><td>Hand over at the last song</td></tr>
                <tr><td>Band</td><td>$25–$50 per musician</td><td>Or one envelope to the bandleader</td></tr>
                <tr><td>Photographer / videographer</td><td>$50–$200 flat, optional</td><td>Often the business owner — a review matters more</td></tr>
                <tr><td>Officiant</td><td>$50–$100</td><td>Or a donation to their house of worship</td></tr>
                <tr><td>Planner / coordinator</td><td>$50–$200, optional</td><td>Not expected if they own the business</td></tr>
                <tr><td>Transport / delivery crew</td><td>15–20% of fare / $5–$20 each</td><td>Check whether gratuity was pre-added</td></tr>
            </tbody>
        </table></div>
        <h2>What couples actually did in 2026</h2>
        <p>Zola's 2026 Wedding Spend Survey asked 720 couples within six months of their weddings who they tipped: <strong>caterers 73%, hair and makeup 71%, photographers 70%, DJ or band 67%, and planners 48%</strong>. Zola suggests budgeting roughly 5–10% of the total wedding cost for tips. Most couples hand out cash on the day, so the practical job is working out the total before the venue day — not after.</p>
        <h2>How to hand it over</h2>
        <p>A week before the wedding, withdraw the cash and put each amount in a labelled envelope with the vendor's name. Ask a trusted person — best man, maid of honour or coordinator — to distribute them as each vendor wraps up. A short thank-you note inside each envelope goes a long way. Use Print / PDF for the envelope list. If a vendor owns the business, a tip is appreciated but not expected; a five-star review and referrals are worth more. This is customary US guidance — tipping expectations differ across Europe, so check local norms for a destination wedding.</p>
        <p>Want to see the whole picture? Put these figures next to the <a href="/tools/wedding-budget-calculator/">budget calculator</a> and the <a href="/tools/wedding-checklist-generator/">planning checklist</a>.</p>
    """,
    "faq": [
        ("Do I tip if there is already a service charge?", "Not necessarily. A service charge of 18–24% is often a house fee, not a gratuity. Ask the catering or venue manager whether it is distributed to staff. If it is, you are covered; if it is not, tip the staff directly — but never pay a separate gratuity line twice."),
        ("How much should I tip a wedding photographer?", "A flat $50–$200 is customary, and it is optional — many photographers own the business and set their own price. Tip second shooters and assistants too; a five-star review and referrals are often worth more than cash."),
        ("Do you tip the wedding DJ?", "Yes, 10–15% of the fee or a flat $50–$150 for a solo DJ. For a band, $25–$50 per musician, or one envelope to the bandleader who splits it. Hand it over at the end of the reception."),
        ("How much do most couples spend on wedding tips in total?", "Ranked guides put a mid-size US wedding between roughly $500 and $1,000+, with some 2026 budget models reaching $1,500–$4,000 for a 100-guest wedding with a full vendor list. Zola suggests budgeting 5–10% of the total wedding cost."),
        ("Should I tip a vendor who owns the business?", "A tip is appreciated but not expected — they set their own price. Focus cash tips on staff and employees. A heartfelt review, referrals, or a thank-you note are excellent alternatives."),
        ("When and how are tips handed out?", "In cash, on the wedding day. Prepare labelled envelopes a week ahead and ask a trusted person — a coordinator, best man or maid of honour — to distribute them as vendors finish. Print the envelope list from this page so nothing is forgotten."),
    ],
    "logic": r"""
window.FT_COMPUTE = function (v) {
  function num(x) { return Math.max(0, parseFloat(x) || 0); }
  var catering = v.service ? 0 : Math.round(num(v.food) * num(v.rate) / 100);
  var bar = v.service ? 0 : Math.round(num(v.bar) * 0.10);
  var hmu = Math.round(num(v.hmu) * 0.18);
  var dj = Math.round(num(v.dj));
  var photo = Math.round(num(v.photo));
  var officiant = Math.round(num(v.officiant));
  var total = catering + bar + hmu + dj + photo + officiant;
  var rows = [
    ['Caterer & wait staff', '$' + catering, v.service ? 'Skipped — contract distributes the service charge' : num(v.rate) + '% of $' + num(v.food)],
    ['Bartenders', '$' + bar, v.service ? 'Skipped — included in contract' : '10% of the bar bill'],
    ['Hair & makeup', '$' + hmu, '18% of the service bill'],
    ['DJ / band leader', '$' + dj, 'Flat envelope'],
    ['Photographer / videographer', '$' + photo, 'Flat, optional'],
    ['Officiant', '$' + officiant, 'Honorarium or donation'],
    ['Total cash to set aside', '$' + total, 'Withdraw this before the wedding day']
  ];
  var lines = ['Wedding tip envelopes', ''];
  rows.forEach(function (r) { lines.push(r[0] + ': ' + r[1] + '  (' + r[2] + ')'); });
  lines.push('', 'Prepare labelled cash envelopes a week ahead. Ask one trusted person to hand them out.');
  return {
    stats: [
      { num: '$' + total, lbl: 'Cash needed', accent: true },
      { num: 6, lbl: 'Envelopes' },
      { num: v.service ? 'Yes' : 'No', lbl: 'Service charge' },
      { num: '$' + (catering + bar), lbl: 'Catering + bar' }
    ],
    head: ['Envelope', 'Amount', 'Basis'], rows: rows,
    note: v.service ? 'Service-charge contracts excluded from catering and bar tips — confirm with the manager that it really reaches the staff.' : 'Customary US amounts, not invoices. Check every contract for an included gratuity, and remember that owner-operators are usually tipped with a review rather than cash.',
    text: lines.join('\n')
  };
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-countdown-widget",
    "name": "Wedding Countdown Maker",
    "short": "Countdown Maker",
    "title": "Wedding Countdown Maker: Shareable Timer & Story Card (Free)",
    "description": "Free wedding countdown maker. Set your date for a live timer, a share link, an iframe embed for your wedding website and a 9:16 story card. No signup.",
    "keywords": "wedding countdown widget, wedding countdown timer, embed countdown on wedding website, days until my wedding, wedding countdown instagram story",
    "og_title": "Free Wedding Countdown Maker — Link, Embed & Story Card",
    "category": "UtilitiesApplication",
    "h1": "Wedding Countdown Maker",
    "lede": "There is often more than a year between the engagement and the day. Make the date feel real — on your wedding website, in the family group chat, or as a story card.",
    "panel_title": "Your countdown",
    "result_title": "Live countdown",
    "mode": "generator",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-date">Wedding date</label><input class="ft-input" type="date" data-ft="date"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-time">Ceremony time</label><input class="ft-input" type="time" value="16:00" data-ft="time" data-ft-default="16:00"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-names">Names / message</label><input class="ft-input" type="text" value="Emma & Noah are getting married" data-ft="names" data-ft-default="Emma & Noah are getting married"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-style">Style</label><select class="ft-select" id="ft-style" data-ft="style"><option value="minimal">Minimal</option><option value="flip">Flip cards</option><option value="neon">Neon</option><option value="editorial">Editorial</option></select></div>
                    <p class="ft-hint">Set the date to today plus one year if you are still choosing. Milestones worth sharing: 6 months, 100 days, 1 month, 1 week.</p>""",
    "article": """
        <h2>What couples actually do with a countdown</h2>
        <p>Ranked widget sites (Countz, Counterdown, WatchIsUp) describe the same set of uses: <strong>a share link in the family group chat, an iframe on the wedding website, a story card on Instagram or TikTok, and a full-screen display at the venue entrance on the day</strong>. The engagement-to-wedding gap in the US averages about 15 months, so a countdown is one of the few things that makes the date feel concrete early on.</p>
        <p>The practical details that separate a good widget from a bad one are time zones (the event's local time, stored as UTC so daylight-saving changes do not shift it), a clean zero state, and no account requirement for guests who open the link.</p>
        <h2>Four ways to use it</h2>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Use</th><th>How</th><th>When</th></tr></thead>
            <tbody>
                <tr><td>Wedding website</td><td>Paste the iframe embed into a Wix, Squarespace, WordPress, Carrd or Notion HTML block</td><td>As soon as the site exists</td></tr>
                <tr><td>Social story</td><td>Export a 9:16 story card screenshot at each milestone</td><td>6 months, 100 days, 1 month, 1 week</td></tr>
                <tr><td>RSVP page</td><td>Put the link beside the RSVP deadline</td><td>When invitations go out</td></tr>
                <tr><td>Venue screen</td><td>Open the link full screen at the entrance</td><td>On the day, until the ceremony starts</td></tr>
            </tbody>
        </table></div>
        <h2>Milestones worth posting</h2>
        <p>Six months, 100 days, one month, one week. Ranked guides also suggest making extra countdowns for planning deadlines — the RSVP date, the final fitting, the menu tasting — each with its own link. Nothing needs installing, and guests never need an account.</p>
        <h2>From the countdown to the keepsake</h2>
        <p>The clock stops at zero, and what remains are the photos. If you are collecting them in one place, the <a href="/tools/wedding-hashtag-generator/">hashtag generator</a> gives guests one tag to use; after the day, a <a href="/blog/wedding-video-from-photos/">cinematic wedding film</a> turns that pile of guest photos into something you will actually watch again.</p>
    """,
    "faq": [
        ("How do I add a countdown to my wedding website?", "Generate it here, copy the iframe embed code, and paste it into an HTML or embed block. It works with WordPress, Wix, Squarespace, Carrd and Notion, and adapts to the available width."),
        ("Can guests see the countdown without an account?", "Yes. The share link is public and read-only — anyone with the link can open it on a phone or computer. Do not put private information such as a home address in the message."),
        ("Does the countdown handle time zones and daylight saving?", "The event time is interpreted in the venue's local time and stored as an instant, so a daylight-saving change between now and the wedding does not shift the day count. Set the ceremony time as your venue's local time."),
        ("What should the countdown show when the day arrives?", "A clean zero state and a short arrival message — never negative days or a frozen 00:00:00 that keeps ticking backwards. This page switches to an arrival message at zero."),
        ("What milestones are worth sharing?", "Six months, 100 days, one month and one week are the four that ranked guides suggest. Screenshot the story card at each one; it is an easy, low-effort way to keep guests excited and the date in their calendars."),
        ("Is anything uploaded to a server?", "No. The date, names and style live in this page and in your browser's local storage. The share link encodes the settings in the URL, so there is no database and no account."),
    ],
    "cta_title": "When the clock hits zero, keep the day.",
    "cta_text": "Turn your engagement and wedding photos into a 60–90 second cinematic film, delivered in 48 hours.",
    "logic": r"""
window.FT_GENERATE = function (v) {
  var dateStr = v.date || '';
  var names = (v.names || '').trim() || 'We are getting married';
  var target = dateStr ? new Date(dateStr + 'T' + (v.time || '16:00') + ':00') : null;
  var valid = target && !isNaN(target.getTime());
  var now = new Date();
  var ms = valid ? target - now : 0;
  var arrived = valid && ms <= 0;
  var days = Math.max(0, Math.floor(ms / 86400000));
  var hours = Math.max(0, Math.floor(ms / 3600000) % 24);
  var mins = Math.max(0, Math.floor(ms / 60000) % 60);
  var secs = Math.max(0, Math.floor(ms / 1000) % 60);
  var clock = arrived ? 'It is today.' : (valid ? days + ' days  ' + String(hours).padStart(2, '0') + 'h  ' + String(mins).padStart(2, '0') + 'm  ' + String(secs).padStart(2, '0') + 's' : 'Set your wedding date to start the countdown.');
  var query = '?d=' + encodeURIComponent(dateStr) + '&t=' + encodeURIComponent(v.time || '16:00') + '&n=' + encodeURIComponent(names) + '&s=' + encodeURIComponent(v.style || 'minimal');
  var share = 'https://weddingai.video/tools/wedding-countdown-widget/' + query;
  var embed = '<iframe src="' + share + '&embed=1" title="Wedding countdown" style="width:100%;max-width:520px;height:150px;border:0;border-radius:12px;" loading="lazy"></iframe>';
  var milestones = [];
  if (valid) {
    [180, 100, 30, 7].forEach(function (d) {
      var m = new Date(target.getTime() - d * 86400000);
      if (m > now) milestones.push(d + ' days out — ' + m.toISOString().slice(0, 10));
    });
  }
  var blocks = [
    { title: 'Live countdown — ' + (v.style || 'minimal'), text: names + '\n\n' + clock },
    { title: 'Share link', text: share },
    { title: 'Embed on your wedding website', text: embed },
    { title: 'Milestone dates to post a 9:16 story card', text: milestones.length ? milestones.join('\n') : 'Set a future date to see 6-month, 100-day, 1-month and 1-week milestones.' }
  ];
  var text = blocks.map(function (b) { return b.title + '\n' + b.text; }).join('\n\n');
  return {
    blocks: blocks,
    stats: [
      { num: valid ? days : '—', lbl: 'Days to go', accent: true },
      { num: valid ? hours : '—', lbl: 'Hours' },
      { num: valid ? mins : '—', lbl: 'Minutes' },
      { num: milestones.length, lbl: 'Milestones' }
    ],
    note: 'Story card: switch your screen to 9:16, use Print / PDF or a screenshot, and post the countdown at each milestone. The share link encodes everything in the URL — no account, no database.',
    text: text
  };
};
window.FT_INIT = function (api) {
  var params = new URLSearchParams(window.location.search);
  var linked = params.get('d');
  if (linked) {
    [['date', 'd'], ['time', 't'], ['names', 'n'], ['style', 's']].forEach(function (pair) {
      var node = api.$('[data-ft="' + pair[0] + '"]');
      var value = params.get(pair[1]);
      if (node && value) node.value = value;
    });
    var fromLink = api.$('[data-ft="date"]');
    if (fromLink) fromLink.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    var dateInput = api.$('[data-ft="date"]');
    if (dateInput && !dateInput.value) {
      var d = new Date(); d.setFullYear(d.getFullYear() + 1);
      dateInput.value = d.toISOString().slice(0, 10);
      dateInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  if (params.get('embed') === '1') document.body.classList.add('ft-embed');
  setInterval(function () { api.recompute(); }, 1000);
};
""",
})

EXTRA_TOOLS.append({
    "slug": "wedding-vendor-questions-checklist",
    "name": "Wedding Vendor Questions Checklist",
    "short": "Vendor Questions",
    "title": "Questions to Ask Wedding Vendors: Copy-Paste Checklist (Free)",
    "description": "Free checklist of the questions to ask every wedding vendor before signing — venue, photographer, caterer, florist, DJ, planner and more, plus red flags.",
    "keywords": "questions to ask wedding vendors, wedding venue questions checklist, questions to ask wedding photographer, vendor interview questions, wedding vendor red flags",
    "og_title": "Free Wedding Vendor Questions — Every Category",
    "category": "ProductivityApplication",
    "h1": "Wedding Vendor Questions Checklist",
    "lede": "Before you sign anything: the questions ranked US planning guides say to ask each vendor, plus the red flags that should end the conversation.",
    "panel_title": "Your shortlist",
    "result_title": "Questions to ask",
    "mode": "checklist",
    "panel": """                    <div class="ft-row"><label class="ft-label" for="ft-vendor">Vendor you are meeting</label><input class="ft-input" type="text" value="Venue" data-ft="vendor" data-ft-default="Venue" placeholder="e.g. Riverside Hall"></div>
                    <div class="ft-row"><label class="ft-label" for="ft-date">Wedding date (optional)</label><input class="ft-input" type="date" data-ft="date"></div>
                    <p class="ft-hint">Tick questions as you ask them. Progress is saved in this browser only — print the list and take it to the meeting.</p>""",
    "article": """
        <h2>Why a written list beats a friendly chat</h2>
        <p>The ranking US guides — A Practical Wedding, Plan In Love, Edel Ryan, Precious Moments Events — all make the same point: <strong>vendors are interviewed before contracts are signed, and the questions that matter are about deliverables, backups and cancellation terms</strong>, not the portfolio. A good vendor answers clearly and in writing; a vague one is a red flag.</p>
        <div class="ft-table-wrap"><table class="ft-table">
            <thead><tr><th>Category</th><th>The question couples most often forget</th></tr></thead>
            <tbody>
                <tr><td>Venue</td><td>What is the strict music curfew, and what is the rain plan?</td></tr>
                <tr><td>Photographer</td><td>Can we see one full wedding gallery, not just highlights?</td></tr>
                <tr><td>Videographer</td><td>Do you capture clean audio of the vows and toasts?</td></tr>
                <tr><td>Caterer</td><td>What exactly is included — staff, linens, tableware, cake cutting?</td></tr>
                <tr><td>Florist</td><td>What happens if the flowers we chose are unavailable?</td></tr>
                <tr><td>DJ / band</td><td>Do you bring backup equipment, and do you act as MC?</td></tr>
                <tr><td>Planner</td><td>How many weddings do you manage that weekend?</td></tr>
                <tr><td>Hair &amp; makeup</td><td>How long per person, and is there a travel fee?</td></tr>
                <tr><td>Cake baker</td><td>Is delivery and setup included, and is there a tasting fee?</td></tr>
            </tbody>
        </table></div>
        <h2>Start every conversation with the same five</h2>
        <ol>
            <li>Are you available on our date, and have you worked at our venue before?</li>
            <li>What exactly is included in this quote or package?</li>
            <li>Do you carry liability insurance and any required permits?</li>
            <li>What is the payment schedule, cancellation and refund policy?</li>
            <li>What is your backup plan if you, your equipment or a key supplier fails?</li>
        </ol>
        <h2>Red flags the ranked guides agree on</h2>
        <p>Vague or missing contracts; no insurance or business licence; slow or evasive communication; pressure to sign on the spot; no online presence or references; and refusal to show a full gallery or a full film rather than a highlight reel. Ask for two recent references and actually call them — the question to ask is not "were they good?" but "how did they handle something going wrong?"</p>
        <p>Once vendors are booked, put their arrival times into the <a href="/tools/wedding-day-timeline-generator/">day-of timeline</a>, their costs into the <a href="/tools/wedding-budget-calculator/">budget calculator</a>, and their envelopes into the <a href="/tools/wedding-vendor-tipping-calculator/">tip calculator</a>.</p>
    """,
    "faq": [
        ("What should I ask a wedding venue before booking?", "Ask what is included in the rental (tables, chairs, linens, lighting), how many hours it covers, the noise curfew and decor restrictions, the indoor rain backup, the alcohol policy, whether other events run simultaneously, and the cancellation terms."),
        ("What should I ask a wedding photographer?", "Ask to see one complete wedding gallery rather than highlights, who will personally shoot your day, whether a second shooter is included, the turnaround time, whether you get full printing rights to high-resolution images, and the backup-equipment plan."),
        ("What are the biggest wedding vendor red flags?", "A vague or missing contract, no liability insurance, slow or evasive replies, pressure to sign immediately, no reviews or references, and refusing to show full deliverables. Any one of these is worth walking away from."),
        ("Should I ask about cancellation and refund policies?", "Always, and get the answer in the contract. Ask about the payment schedule, what happens if the vendor cannot fulfil the commitment, and whether the deposit is transferable to a new date."),
        ("How many vendors should I interview?", "Two to three per category is a sensible shortlist for a US wedding. Use the same question list for each so you can compare answers directly rather than relying on who gave the best sales pitch."),
        ("Can I print this checklist for the meeting?", "Yes. Print / PDF gives a clean list of every question with tick boxes, and Copy result gives plain text for a shared note. Your ticks are saved only in this browser."),
    ],
    "logic": r"""
window.FT_GROUPS = [
  { title: 'Ask every vendor (the universal five)', items: [
    { id: 'q1', text: 'Are you available on our date, and have you worked at our venue before?' },
    { id: 'q2', text: 'What exactly is included in this quote or package?' },
    { id: 'q3', text: 'Do you carry liability insurance and any required permits?' },
    { id: 'q4', text: 'What is the payment schedule, cancellation and refund policy?' },
    { id: 'q5', text: 'What is your backup plan if you or your equipment fails?' },
    { id: 'q6', text: 'Can we have two references from recent weddings?' }
  ]},
  { title: 'Venue', items: [
    { id: 'q7', text: 'What is the seated-dinner capacity versus a cocktail reception?' },
    { id: 'q8', text: 'Are tables, chairs, linens and dinnerware included?' },
    { id: 'q9', text: 'What is the rain / weather contingency for outdoor spaces?' },
    { id: 'q10', text: 'What time can vendors set up, and what is the strict music curfew?' },
    { id: 'q11', text: 'Is the site exclusive to us, or are other events running?' },
    { id: 'q12', text: 'What is the alcohol policy — in-house bar or BYOB, corkage?' }
  ]},
  { title: 'Photographer & videographer', items: [
    { id: 'q13', text: 'Can we see one complete gallery / full film, not just highlights?' },
    { id: 'q14', text: 'Will you personally shoot our day, and is there a second shooter?' },
    { id: 'q15', text: 'How many hours of coverage, and what is the delivery turnaround?' },
    { id: 'q16', text: 'Do we get full printing rights to the high-resolution images?' },
    { id: 'q17', text: 'Do you capture clean audio for the vows and toasts?' },
    { id: 'q18', text: 'What backup equipment is on site, and do you keep raw footage?' }
  ]},
  { title: 'Caterer & bar', items: [
    { id: 'q19', text: 'Is a tasting included, and is there a fee credited if we book?' },
    { id: 'q20', text: 'How do you handle dietary restrictions and allergies?' },
    { id: 'q21', text: 'Are staff, setup, cleanup, linens and tableware included?' },
    { id: 'q22', text: 'What is the staff-to-guest ratio for plated versus buffet?' },
    { id: 'q23', text: 'Is cake cutting included, and is the service charge a gratuity?' }
  ]},
  { title: 'Florist & cake', items: [
    { id: 'q24', text: 'Is there a minimum budget, and can you suggest seasonal alternatives?' },
    { id: 'q25', text: 'What happens if a flower we chose is unavailable?' },
    { id: 'q26', text: 'Are delivery, setup, rentals and late breakdown included?' },
    { id: 'q27', text: 'Can ceremony arrangements be repurposed for the reception?' },
    { id: 'q28', text: 'Will you coordinate with the florist / venue on delivery day?' }
  ]},
  { title: 'DJ, band & ceremony music', items: [
    { id: 'q29', text: 'Do you act as MC for announcements, and do you take requests?' },
    { id: 'q30', text: 'Do you provide your own sound, microphones and lighting?' },
    { id: 'q31', text: 'What is the backup plan if equipment fails or you cannot perform?' },
    { id: 'q32', text: 'What are the overtime rates and the do-not-play list process?' }
  ]},
  { title: 'Planner, hair & makeup', items: [
    { id: 'q33', text: 'What is the difference between full, partial and month-of coordination?' },
    { id: 'q34', text: 'How many weddings do you manage on the same weekend?' },
    { id: 'q35', text: 'Do you create the day-of timeline and floor plan?' },
    { id: 'q36', text: 'Is a trial included, and is there a travel fee?' },
    { id: 'q37', text: 'How long do you allocate per person, and is there an assistant?' }
  ]},
  { title: 'Red flags — end the conversation if you see these', items: [
    { id: 'q38', text: 'Vague or missing written contract' },
    { id: 'q39', text: 'No liability insurance or business licence' },
    { id: 'q40', text: 'Slow, evasive or pressuring communication' },
    { id: 'q41', text: 'No online presence, reviews or references' },
    { id: 'q42', text: 'Refusal to show a full gallery or full deliverable' }
  ]}
];
window.FT_INIT = function (api) {
  var wrap = api.$('#ft-progress-wrap');
  if (wrap) wrap.style.display = '';
  var note = api.$('#ft-note');
  if (note) {
    note.style.display = '';
    note.textContent = 'Ask the same questions of two to three vendors per category so the answers are comparable. Get every answer in the contract, not just in an email.';
  }
};
""",
})
