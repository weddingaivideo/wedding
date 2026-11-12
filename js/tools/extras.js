/* Extras for the free planning tools (v1.0).
   Adds real .pdf / .ics downloads, editable timelines, a countdown-week
   checklist view. Loaded after free-tools.js; CSP is nonce-only so there
   are no inline handlers and no external dependencies.

   Per-page opt-in lives in window.FT_EXTRAS:
     { pdf:true, ics:true, editable:true, weekView:true,
       eventTitle:'Wedding day', weekMap:[52,40,28,16,8,4,1] }
   Button labels are static data-i18n markup, so the middleware translates
   them before this file ever runs. */
(function () {
  'use strict';

  var cfg = window.FT_EXTRAS || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var slug = (cfg.slug || (location.pathname.match(/tools\/([a-z0-9-]+)/) || [])[1] || 'wedding-tool');

  function label(id, fallback) {
    var n = document.getElementById(id);
    return (n && n.textContent.trim()) || fallback;
  }
  function toast(msg) {
    var n = document.createElement('div');
    n.className = 'ft-toast';
    n.textContent = msg;
    n.setAttribute('role', 'status');
    document.body.appendChild(n);
    setTimeout(function () { n.classList.add('is-out'); }, 1900);
    setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, 2400);
  }
  function saveBlob(parts, name, mime) {
    var blob = new Blob(parts, { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  /* ------------------------------------------------------------------
     Real PDF download, no libraries and no font embedding.
     The page text is rasterised with canvas (so CJK / Thai / Arabic /
     Devanagari all work with the browser's own fonts) and each page image
     is wrapped in a minimal PDF 1.4 container with DCTDecode (JPEG).
  ------------------------------------------------------------------ */
  function bytes(str) {
    var out = new Uint8Array(str.length);
    for (var i = 0; i < str.length; i++) out[i] = str.charCodeAt(i) & 0xff;
    return out;
  }
  function fromBase64(b64) {
    var bin = atob(b64), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function concat(chunks) {
    var len = chunks.reduce(function (n, c) { return n + c.length; }, 0);
    var out = new Uint8Array(len), at = 0;
    chunks.forEach(function (c) { out.set(c, at); at += c.length; });
    return out;
  }
  function pdfEscape(s) { return String(s).replace(/([\\()])/g, '\\$1'); }

  function resultText() {
    var t = window.FT_LAST_TEXT || '';
    if (!t.trim()) {
      var out = $('#ft-output');
      if (out) t = out.innerText || out.textContent || '';
    }
    return t;
  }

  function wrapLines(ctx, text, maxW) {
    var lines = [];
    String(text == null ? '' : text).split('\n').forEach(function (para) {
      if (!para) { lines.push(''); return; }
      var words = para.split(/(\s+)/), line = '';
      words.forEach(function (w) {
        var trial = line + w;
        if (line && ctx.measureText(trial).width > maxW) { lines.push(line); line = w.trimStart(); }
        else line = trial;
      });
      lines.push(line);
      // A very long unbroken token (URLs, CJK runs) still needs splitting.
      var last = lines.length - 1;
      while (ctx.measureText(lines[last]).width > maxW && lines[last].length > 1) {
        var cut = lines[last].length - 1, piece = lines[last];
        while (cut > 1 && ctx.measureText(piece.slice(0, cut)).width > maxW) cut--;
        lines[last] = piece.slice(0, cut);
        lines.splice(last + 1, 0, piece.slice(cut));
        last++;
      }
    });
    return lines;
  }

  function downloadPdf() {
    var text = resultText();
    if (!text.trim()) { toast(label('ft-pdf', 'Download .pdf') + ' — ' + (window.FT_EMPTY_HINT || 'Nothing to export yet')); return; }
    var W = 794, H = 1123, M = 58, lh = 21;
    var cvs = document.createElement('canvas');
    cvs.width = W; cvs.height = H;
    var ctx = cvs.getContext('2d');
    var font = '15px "Noto Sans", "Segoe UI", Arial, sans-serif';
    ctx.font = font;
    var lines = wrapLines(ctx, text, W - M * 2);
    var perPage = Math.floor((H - M * 2 - 54) / lh);
    var pages = Math.max(1, Math.ceil(lines.length / perPage));
    var jpegs = [];
    var title = (document.title || slug).replace(/\s*[|｜].*$/, '').trim();

    for (var p = 0; p < pages; p++) {
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#1c1917'; ctx.font = 'bold 20px "Noto Sans", "Segoe UI", Arial, sans-serif';
      ctx.fillText(title, M, M + 4);
      ctx.strokeStyle = '#e7e2dc'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(M, M + 18); ctx.lineTo(W - M, M + 18); ctx.stroke();
      ctx.font = font; ctx.fillStyle = '#292524';
      var chunk = lines.slice(p * perPage, (p + 1) * perPage);
      chunk.forEach(function (ln, i) { ctx.fillText(ln, M, M + 54 + i * lh); });
      ctx.fillStyle = '#78716c'; ctx.font = '12px Arial, sans-serif';
      ctx.fillText((p + 1) + ' / ' + pages + '  ·  ' + location.hostname, M, H - M / 2);
      jpegs.push(cvs.toDataURL('image/jpeg', 0.86).split(',')[1]);
    }

    var objs = [], objOffsets = [], size = 0;
    function push(s) { objOffsets.push(size); var b = bytes(s); size += b.length; objs.push(b); }
    function pushBin(s, bin) { objOffsets.push(size); var a = bytes(s); size += a.length + bin.length; objs.push(a); objs.push(bin); }
    function tailChunk(s) { var b = bytes(s); size += b.length; objs.push(b); }

    tailChunk('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n');
    // Object ids: 1 catalog, 2 pages, then 3 per page (page, content, image).
    var kids = [], first = 3;
    for (var q = 0; q < pages; q++) kids.push((first + q * 3) + ' 0 R');
    push('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n');
    push('2 0 obj\n<< /Type /Pages /Kids [' + kids.join(' ') + '] /Count ' + pages + ' >>\nendobj\n');
    for (var q2 = 0; q2 < pages; q2++) {
      var pid = first + q2 * 3, cid = pid + 1, iid = pid + 2;
      push(pid + ' 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] ' +
           '/Resources << /XObject << /Im0 ' + iid + ' 0 R >> >> /Contents ' + cid + ' 0 R >>\nendobj\n');
      var stream = 'q 595 0 0 842 0 0 cm /Im0 Do Q\n';
      push(cid + ' 0 obj\n<< /Length ' + stream.length + ' >>\nstream\n' + stream + 'endstream\nendobj\n');
      var img = fromBase64(jpegs[q2]);
      pushBin(iid + ' 0 obj\n<< /Type /XObject /Subtype /Image /Width ' + W + ' /Height ' + H +
              ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ' + img.length +
              ' >>\nstream\n', img);
      tailChunk('\nendstream\nendobj\n');
    }
    var xref = size;
    var tail = 'xref\n0 ' + (objOffsets.length + 1) + '\n0000000000 65535 f \n';
    objOffsets.forEach(function (o) { tail += ('0000000000' + o).slice(-10) + ' 00000 n \n'; });
    tail += 'trailer\n<< /Size ' + (objOffsets.length + 1) + ' /Root 1 0 R >>\nstartxref\n' + xref + '\n%%EOF\n';
    saveBlob([concat(objs), bytes(tail)], slug + '.pdf', 'application/pdf');
  }

  /* ------------------------------------------------------------------
     .ics calendar export for the day timeline.
     Reads the rendered result table (time | what | who), so edits made by
     the drag/editor below are reflected automatically.
  ------------------------------------------------------------------ */
  function icsPad(n) { return String(n).padStart(2, '0'); }
  function icsStamp(d, min) {
    var hh = Math.floor(((min % 1440) + 1440) % 1440 / 60);
    var mm = ((min % 1440) + 1440) % 1440 % 60;
    var day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    if (min >= 1440) day.setDate(day.getDate() + Math.floor(min / 1440));
    if (min < 0) day.setDate(day.getDate() + Math.floor(min / 1440));
    return day.getFullYear() + icsPad(day.getMonth() + 1) + icsPad(day.getDate()) +
           'T' + icsPad(hh) + icsPad(mm) + '00';
  }
  function icsEscape(s) {
    return String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/;/g, '\\;')
      .replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  }
  function icsFold(line) {
    // 75 octets per line; keep it ASCII-safe by measuring UTF-8 bytes.
    var out = '', buf = '', n = 0;
    for (var i = 0; i < line.length; i++) {
      var ch = line[i], w = unescape(encodeURIComponent(ch)).length;
      if (n + w > 74) { out += buf + '\r\n '; buf = ''; n = 1; }
      buf += ch; n += w;
    }
    return out + buf;
  }
  function readDate() {
    var f = $('[data-ft="date"]');
    var raw = f && f.value;
    if (raw) { var p = raw.split('-'); if (p.length === 3) return new Date(+p[0], +p[1] - 1, +p[2]); }
    var d = new Date(); d.setDate(d.getDate() + 180); return d;
  }
  /* A cell can hold a time <input> (editable rows) and a trailing span of
     move buttons. Reading textContent would lose the edited time and leak
     the arrow glyphs into the "who" column, so read the input value and
     only the cell's own text nodes. */
  function cellText(td) {
    var inp = td.querySelector('input');
    if (inp) return (inp.value || '').trim();
    var out = '';
    Array.prototype.forEach.call(td.childNodes, function (n) {
      if (n.nodeType === 3) out += n.nodeValue;
    });
    return out.trim() || td.textContent.trim();
  }
  function downloadIcs() {
    var table = $('#ft-table table');
    if (!table) { toast('No schedule yet'); return; }
    var rows = $$('tbody tr', table).map(function (tr) {
      return $$('td', tr).map(cellText);
    }).filter(function (r) { return r.length >= 2 && /^\d{1,2}:\d{2}$/.test(r[0]); });
    if (!rows.length) { toast('No schedule yet'); return; }
    var d = readDate();
    function mins(t) { var p = t.split(':'); return (+p[0]) * 60 + (+p[1]); }
    var stamp = function () {
      var x = new Date(), f = function (n) { return icsPad(n); };
      return x.getUTCFullYear() + f(x.getUTCMonth() + 1) + f(x.getUTCDate()) + 'T' +
             f(x.getUTCHours()) + f(x.getUTCMinutes()) + f(x.getUTCSeconds()) + 'Z';
    }();
    var L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//WeddingAI.video//Wedding Day Timeline//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:' + icsEscape(cfg.eventTitle || 'Wedding day')];
    var dayOffset = 0, prev = null;
    rows.forEach(function (r, i) {
      var raw = mins(r[0]);
      // A timeline that runs past midnight wraps 23:50 -> 00:10. Keep the
      // calendar chronological instead of folding those events onto day one.
      if (prev !== null && raw < prev) dayOffset += 1440;
      prev = raw;
      var start = raw + dayOffset;
      var nextRaw = (i + 1 < rows.length) ? mins(rows[i + 1][0]) : raw + 30;
      var end = nextRaw + dayOffset + (nextRaw < raw ? 1440 : 0);
      if (end <= start) end = start + 30;
      L.push('BEGIN:VEVENT');
      L.push('UID:' + Date.now() + '-' + i + '-' + slug + '@weddingai.video');
      L.push('DTSTAMP:' + stamp);
      L.push('DTSTART:' + icsStamp(d, start));
      L.push('DTEND:' + icsStamp(d, end));
      L.push('SUMMARY:' + icsEscape(r[1]));
      L.push('DESCRIPTION:' + icsEscape(r[2] ? 'Responsible: ' + r[2] : ''));
      L.push('END:VEVENT');
    });
    L.push('END:VCALENDAR');
    saveBlob([L.map(icsFold).join('\r\n') + '\r\n'], slug + '.ics', 'text/calendar;charset=utf-8');
  }

  /* ------------------------------------------------------------------
     Editable timeline: drag rows, move up/down, edit the time cell.
     Every mutation re-syncs FT_LAST_TEXT so copy/.txt/.pdf/.ics agree.
  ------------------------------------------------------------------ */
  function syncFromTable() {
    var table = $('#ft-table table');
    if (!table) return;
    var head = $$('thead th', table).map(function (th) { return th.textContent.trim(); });
    var rows = $$('tbody tr', table).map(function (tr) {
      return $$('td', tr).map(cellText);
    });
    var lines = [];
    if (head.length) lines.push(head.join('\t'));
    rows.forEach(function (r) { lines.push(r.join('\t')); });
    // The human-readable version is what copy/pdf should show.
    var human = [cfg.eventTitle || 'Wedding day timeline', ''];
    rows.forEach(function (r) { human.push(r[0] + '  ' + r[1] + (r[2] ? '  [' + r[2] + ']' : '')); });
    window.FT_LAST_TEXT = human.join('\n');
    window.FT_TABLE_TEXT = lines.join('\n');
  }
  var editObserving = false;
  function attachEditable() {
    var table = $('#ft-table table');
    if (!table) return;
    var tbody = table.querySelector('tbody');
    if (!tbody || tbody.dataset.ftEdit === '1') return;
    tbody.dataset.ftEdit = '1';
    $$('tr', tbody).forEach(function (tr, idx) {
      tr.setAttribute('draggable', 'true');
      tr.dataset.ftRow = String(idx);
      var td = tr.querySelector('td');
      if (td && /^\d{1,2}:\d{2}$/.test(td.textContent.trim())) {
        var v = td.textContent.trim();
        td.textContent = '';
        var inp = document.createElement('input');
        inp.type = 'time'; inp.value = v; inp.className = 'ft-time-edit';
        inp.setAttribute('aria-label', 'Time');
        inp.addEventListener('change', syncFromTable);
        td.appendChild(inp);
      }
      var last = tr.lastElementChild;
      if (last) {
        var tools = document.createElement('span');
        tools.className = 'ft-row-tools';
        [['↑', -1, 'Move up'], ['↓', 1, 'Move down']].forEach(function (spec) {
          var b = document.createElement('button');
          b.type = 'button'; b.className = 'ft-row-btn';
          b.textContent = spec[0]; b.title = spec[2]; b.setAttribute('aria-label', spec[2]);
          b.addEventListener('click', function () {
            if (spec[1] < 0) {
              var prev = tr.previousElementSibling;
              if (prev) tbody.insertBefore(tr, prev);
            } else {
              var next = tr.nextElementSibling;
              if (next) tbody.insertBefore(next, tr);
            }
            syncFromTable();
          });
          tools.appendChild(b);
        });
        last.appendChild(tools);
      }
    });
    var dragged = null;
    tbody.addEventListener('dragstart', function (e) {
      dragged = e.target.closest ? e.target.closest('tr') : null;
      if (dragged) { dragged.classList.add('is-dragging'); e.dataTransfer.effectAllowed = 'move'; }
    });
    tbody.addEventListener('dragover', function (e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
    tbody.addEventListener('drop', function (e) {
      e.preventDefault();
      var target = e.target.closest ? e.target.closest('tr') : null;
      if (!dragged || !target || dragged === target) return;
      var rows = $$('tr', tbody);
      if (rows.indexOf(dragged) < rows.indexOf(target)) tbody.insertBefore(dragged, target.nextSibling);
      else tbody.insertBefore(dragged, target);
      dragged.classList.remove('is-dragging');
      syncFromTable();
    });
    tbody.addEventListener('dragend', function () {
      if (dragged) dragged.classList.remove('is-dragging');
      dragged = null;
    });
    syncFromTable();
  }
  function makeEditable() {
    attachEditable();
    if (editObserving || typeof MutationObserver === 'undefined') return;
    var host = $('#ft-table');
    if (!host) return;
    editObserving = true;
    // recompute() replaces the whole table; re-attach to the new tbody.
    new MutationObserver(function () { attachEditable(); }).observe(host, { childList: true });
  }

  /* ------------------------------------------------------------------
     Countdown-week view for the checklist.
     Groups are mapped to weeks-before-the-wedding; with a wedding date the
     current week is highlighted and the matching group is expanded.
  ------------------------------------------------------------------ */
  function weekView() {
    var host = $('#ft-groups');
    if (!host) return;
    var toggle = document.getElementById('ft-week-toggle');
    if (!toggle) return;
    var groups = $$('.ft-group', host);
    var map = cfg.weekMap || [52, 40, 28, 16, 8, 4, 1];
    function weeksLeft() {
      var f = $('[data-ft="date"]');
      if (!f || !f.value) return null;
      var p = f.value.split('-');
      var d = p.length === 3 ? new Date(+p[0], +p[1] - 1, +p[2]) : null;
      return d ? Math.max(0, Math.round((d - new Date()) / 604800000)) : null;
    }
    function paint() {
      var on = host.classList.toggle('is-week-view', toggle.getAttribute('aria-pressed') === 'true');
      var left = weeksLeft();
      groups.forEach(function (g, i) {
        var w = map[Math.min(i, map.length - 1)];
        var tag = g.querySelector('.ft-week-tag');
        if (!tag) {
          tag = document.createElement('span');
          tag.className = 'ft-week-tag';
          var head = g.querySelector('.ft-group-head');
          if (head) head.insertBefore(tag, head.firstChild);
        }
        tag.textContent = on ? ('T-' + w + 'w') : '';
        var nextW = (i + 1 < map.length) ? map[i + 1] : -1;
        g.classList.toggle('is-current-week', on && left !== null && left <= w && left > nextW);
      });
      var hint = document.getElementById('ft-week-hint');
      if (hint) {
        hint.style.display = on ? '' : 'none';
        var a = document.getElementById('ft-week-hint-nodate');
        var b = document.getElementById('ft-week-hint-yesdate');
        if (a) a.style.display = (on && left === null) ? '' : 'none';
        if (b) b.style.display = (on && left !== null) ? '' : 'none';
      }
    }
    toggle.addEventListener('click', function () {
      toggle.setAttribute('aria-pressed', toggle.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      paint();
    });
    var dateField = $('[data-ft="date"]');
    if (dateField) dateField.addEventListener('change', paint);
    paint();
  }

  function start() {
    var pdfBtn = document.getElementById('ft-pdf');
    if (cfg.pdf !== false && pdfBtn) pdfBtn.addEventListener('click', downloadPdf);
    var icsBtn = document.getElementById('ft-ics');
    if (icsBtn) icsBtn.addEventListener('click', downloadIcs);
    if (cfg.editable) makeEditable();
    if (cfg.weekView) weekView();
    $$('.ft-region-dismiss').forEach(function (b) {
      b.addEventListener('click', function () {
        var n = b.closest ? b.closest('.ft-region-note') : null;
        if (n) n.hidden = true;
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
