/* Shared runtime for the free planning tools.
   Each page declares:
     window.FT_CONFIG   = { mode: 'calc'|'generator'|'checklist', storageKey, ... }
     window.FT_COMPUTE  = function(values){ ... }        // calc mode
     window.FT_GENERATE = function(values, variant){ ... } // generator mode
     window.FT_GROUPS   = [ { title, items:[{id,text}] } ] // checklist mode
     window.FT_INIT     = function(api){ ... }            // optional per-page hook
   No inline event handlers: CSP is nonce-only. */
(function () {
  'use strict';

  var cfg = window.FT_CONFIG || {};
  var mode = cfg.mode || 'calc';
  var storageKey = cfg.storageKey || 'ft-tool';
  var variant = 0;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }
  function readStore(key, fallback) {
    try { var raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback; }
    catch (e) { return fallback; }
  }
  function writeStore(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private mode */ }
  }

  /* ---------- form values ---------- */
  function fieldNodes() { return $$('[data-ft]'); }
  function readValues() {
    var out = {};
    fieldNodes().forEach(function (node) {
      var name = node.getAttribute('data-ft');
      if (node.type === 'checkbox') out[name] = node.checked;
      else if (node.type === 'radio') { if (node.checked) out[name] = node.value; }
      else if (node.type === 'number' || node.type === 'range') out[name] = parseFloat(node.value) || 0;
      else out[name] = node.value;
    });
    return out;
  }
  function restoreValues() {
    var saved = readStore(storageKey + ':values', null);
    if (!saved) return;
    fieldNodes().forEach(function (node) {
      var name = node.getAttribute('data-ft');
      if (!Object.prototype.hasOwnProperty.call(saved, name)) return;
      if (node.type === 'checkbox') node.checked = !!saved[name];
      else if (node.type === 'radio') node.checked = (node.value === saved[name]);
      else node.value = saved[name];
    });
  }
  function saveValues() { writeStore(storageKey + ':values', readValues()); }

  /* ---------- result rendering ---------- */
  function renderStats(stats) {
    var box = $('#ft-stats');
    if (!box) return;
    box.textContent = '';
    (stats || []).forEach(function (s) {
      var card = el('div', 'ft-stat' + (s.accent ? ' is-accent' : ''));
      card.appendChild(el('span', 'ft-stat-num', s.num));
      card.appendChild(el('span', 'ft-stat-lbl', s.lbl));
      box.appendChild(card);
    });
  }
  function renderTable(head, rows) {
    var box = $('#ft-table');
    if (!box) return;
    box.textContent = '';
    if (!rows || !rows.length) return;
    var table = el('table', 'ft-table');
    var thead = el('thead');
    var htr = el('tr');
    (head || []).forEach(function (h) { htr.appendChild(el('th', null, h)); });
    thead.appendChild(htr);
    table.appendChild(thead);
    var tbody = el('tbody');
    rows.forEach(function (row) {
      var tr = el('tr');
      row.forEach(function (cell) { tr.appendChild(el('td', null, cell)); });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    box.appendChild(table);
  }
  function renderBlocks(blocks) {
    var box = $('#ft-output');
    if (!box) return;
    box.textContent = '';
    (blocks || []).forEach(function (b) {
      if (b.title) box.appendChild(el('h3', null, b.title));
      box.appendChild(el('div', 'ft-output', b.text));
    });
  }
  function renderNote(note) {
    var box = $('#ft-note');
    if (!box) return;
    box.textContent = note || '';
    box.style.display = note ? '' : 'none';
  }
  function setCopyText(text) { window.FT_LAST_TEXT = text || ''; }

  /* ---------- calc / generator ---------- */
  function recompute() {
    var values = readValues();
    saveValues();
    if (mode === 'calc' && typeof window.FT_COMPUTE === 'function') {
      var r = window.FT_COMPUTE(values) || {};
      renderStats(r.stats);
      renderTable(r.head, r.rows);
      renderNote(r.note);
      setCopyText(r.text || buildTextFromRows(r.head, r.rows));
    } else if (mode === 'generator' && typeof window.FT_GENERATE === 'function') {
      var g = window.FT_GENERATE(values, variant) || {};
      renderBlocks(g.blocks);
      renderStats(g.stats);
      renderNote(g.note);
      setCopyText(g.text || (g.blocks || []).map(function (b) { return b.text; }).join('\n\n'));
    }
  }
  function buildTextFromRows(head, rows) {
    if (!rows || !rows.length) return '';
    var lines = [];
    if (head && head.length) lines.push(head.join('\t'));
    rows.forEach(function (r) { lines.push(r.join('\t')); });
    return lines.join('\n');
  }

  /* ---------- checklist ---------- */
  function initChecklist() {
    var groups = window.FT_GROUPS || [];
    var host = $('#ft-groups');
    if (!host) return;
    var done = readStore(storageKey + ':done', {});
    host.textContent = '';

    function updateProgress() {
      var total = 0, checked = 0;
      $$('.ft-item input[type="checkbox"]', host).forEach(function (cb) {
        total++; if (cb.checked) checked++;
      });
      var pct = total ? Math.round(checked * 100 / total) : 0;
      var bar = $('#ft-progress-fill');
      var label = $('#ft-progress-label');
      if (bar) bar.style.width = pct + '%';
      if (label) label.textContent = checked + ' of ' + total + ' done (' + pct + '%)';
    }

    groups.forEach(function (group) {
      var wrap = el('div', 'ft-group');
      var head = el('div', 'ft-group-head');
      head.appendChild(el('span', null, group.title));
      head.appendChild(el('span', 'ft-count', group.items.length + ' tasks'));
      wrap.appendChild(head);
      var body = el('div', 'ft-group-body');
      group.items.forEach(function (item) {
        var line = el('label', 'ft-item');
        var cb = el('input');
        cb.type = 'checkbox';
        cb.checked = !!done[item.id];
        cb.setAttribute('data-ft-item', item.id);
        var txt = el('span', null, item.text);
        line.appendChild(cb);
        line.appendChild(txt);
        body.appendChild(line);
        cb.addEventListener('change', function () {
          done[item.id] = cb.checked;
          if (!cb.checked) delete done[item.id];
          line.classList.toggle('is-done', cb.checked);
          writeStore(storageKey + ':done', done);
          updateProgress();
        });
        line.classList.toggle('is-done', cb.checked);
      });
      wrap.appendChild(body);
      host.appendChild(wrap);
    });
    updateProgress();
    setCopyText(groups.map(function (g) {
      return g.title + '\n' + g.items.map(function (i) { return '[ ] ' + i.text; }).join('\n');
    }).join('\n\n'));
  }

  /* ---------- actions ---------- */
  function copyText(btn) {
    var text = window.FT_LAST_TEXT || '';
    if (!text) return;
    function done(ok) {
      if (!btn) return;
      var old = btn.textContent;
      btn.textContent = ok ? 'Copied ✓' : 'Select & copy';
      setTimeout(function () { btn.textContent = old; }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
    } else {
      var ta = el('textarea');
      ta.value = text;
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      done(ok);
    }
  }
  function downloadText() {
    var text = window.FT_LAST_TEXT || '';
    if (!text) return;
    var blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = el('a');
    a.href = url;
    a.download = (cfg.downloadName || 'wedding-tool') + '.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  function resetAll() {
    try {
      localStorage.removeItem(storageKey + ':values');
      localStorage.removeItem(storageKey + ':done');
    } catch (e) { /* private mode */ }
    variant = 0;
    fieldNodes().forEach(function (node) {
      if (node.type === 'checkbox') node.checked = !!node.getAttribute('data-ft-default');
      else if (node.type === 'radio') node.checked = !!node.getAttribute('data-ft-default');
      else if (node.hasAttribute('data-ft-default')) node.value = node.getAttribute('data-ft-default');
    });
    if (mode === 'checklist') initChecklist(); else recompute();
  }

  function bind() {
    fieldNodes().forEach(function (node) {
      ['input', 'change'].forEach(function (evt) { node.addEventListener(evt, recompute); });
    });
    $$('[data-ft-chip]').forEach(function (chip) {
      chip.addEventListener('click', function () {
        var target = chip.getAttribute('data-ft-chip');
        var value = chip.getAttribute('data-ft-value');
        var node = $('[data-ft="' + target + '"]');
        if (node) {
          node.value = value;
          node.dispatchEvent(new Event('input', { bubbles: true }));
        }
        $$('[data-ft-chip="' + target + '"]').forEach(function (c) { c.classList.remove('is-active'); });
        chip.classList.add('is-active');
      });
    });
    var copyBtn = $('#ft-copy');
    if (copyBtn) copyBtn.addEventListener('click', function () { copyText(copyBtn); });
    var dlBtn = $('#ft-download');
    if (dlBtn) dlBtn.addEventListener('click', downloadText);
    var printBtn = $('#ft-print');
    if (printBtn) printBtn.addEventListener('click', function () { window.print(); });
    var resetBtn = $('#ft-reset');
    if (resetBtn) resetBtn.addEventListener('click', resetAll);
    var againBtn = $('#ft-again');
    if (againBtn) againBtn.addEventListener('click', function () { variant++; recompute(); });
  }

  function start() {
    restoreValues();
    if (mode === 'checklist') initChecklist();
    bind();
    recompute();
    if (typeof window.FT_INIT === 'function') {
      window.FT_INIT({ recompute: recompute, values: readValues, copy: copyText, download: downloadText, el: el, $: $ });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
