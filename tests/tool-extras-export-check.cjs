/* Headless regression for js/tools/extras.js: the real .pdf writer and the
   .ics calendar writer. Run with `node tests/tool-extras-export-check.cjs`.

   No DOM library is needed - only the small surface extras.js touches is
   stubbed. Both exports are validated in memory; nothing is written to the
   repo, so this also runs inside a clean detached worktree. */
'use strict';
const assert = require('assert');
const JPEG = '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwcJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPDs0NDT/wAALCAABAAEBAREA/8QAFAABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAA/AKp//9k=';

let lastBlob = null;
global.Blob = class Blob {
  constructor(parts, opts) { this.parts = parts; this.type = opts && opts.type; lastBlob = this; }
};
global.URL.createObjectURL = () => 'blob:test';
global.URL.revokeObjectURL = () => {};
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');
global.location = { pathname: '/tools/wedding-day-timeline-generator/', hostname: 'weddingai.video' };
global.MutationObserver = undefined;

const handlers = {};
function element(id) {
  return {
    id, textContent: '', className: '', style: {}, dataset: {},
    addEventListener: (e, fn) => { handlers[id + ':' + e] = fn; },
    setAttribute() {}, getAttribute() { return null; },
    appendChild() {}, removeChild() {}, click() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    closest() { return null; },
  };
}
const canvas = {
  width: 0, height: 0,
  getContext: () => ({
    font: '', fillStyle: '', strokeStyle: '', lineWidth: 1,
    measureText: (s) => ({ width: String(s).length * 7 }),
    fillText() {}, fillRect() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {},
  }),
  toDataURL: () => 'data:image/jpeg;base64,' + JPEG,
};
function cell(text, inputValue) {
  return {
    childNodes: [{ nodeType: 3, nodeValue: text }, { nodeType: 1 }],
    textContent: text + '\u2191\u2193',      // glyphs from the move buttons
    querySelector: (sel) => (sel === 'input' && inputValue ? { value: inputValue } : null),
  };
}
function row(cols) {
  const tds = cols.map((c, i) => cell(c.text, i === 0 ? c.time : null));
  return { querySelectorAll: (sel) => (sel === 'td' ? tds : []),
    querySelector: () => null, lastElementChild: tds[tds.length - 1],
    setAttribute() {}, dataset: {} };
}
const rows = [
  row([{ text: '', time: '09:00' }, { text: 'Hair & makeup begins' }, { text: 'Stylists' }]),
  row([{ text: '16:00', time: null }, { text: 'Ceremony begins' }, { text: 'Everyone' }]),
  row([{ text: '00:15', time: null }, { text: 'Grand exit' }, { text: 'Everyone' }]),
];
const tbody = { querySelectorAll: (sel) => (sel === 'tr' ? rows : []),
  dataset: {}, addEventListener() {}, insertBefore() {} };
const table = { querySelectorAll: (sel) => (sel === 'tbody tr' ? rows : []),
  querySelector: () => tbody, tHead: null };
const dateInput = { value: '2026-06-20' };

global.document = {
  readyState: 'complete', title: 'Wedding Day Timeline | WeddingAI.video',
  body: { appendChild() {}, removeChild() {} },
  getElementById: (id) => (id === 'ft-pdf' || id === 'ft-ics' ? element(id) : null),
  querySelector: (sel) => {
    if (sel === '#ft-table table' || sel === '#ft-table') return table;
    if (sel === '[data-ft="date"]') return dateInput;
    return null;
  },
  querySelectorAll: () => [],
  createElement: (tag) => (tag === 'canvas' ? canvas : element(tag)),
  addEventListener() {},
};
global.window = {
  FT_EXTRAS: { slug: 'wedding-day-timeline-generator', pdf: true, ics: true,
    eventTitle: 'Wedding day timeline' },
  FT_LAST_TEXT: Array.from({ length: 130 }, (_, i) =>
    i % 9 === 0 ? '' : `Line ${i + 1}: wedding notes 2026, 150-250 words, émojis 中文 תאילנדית.`).join('\n'),
  FT_EMPTY_HINT: 'Nothing to export yet',
};

require('../js/tools/extras.js');

/* ---- PDF: header, xref table and every object offset ---- */
const pdfFn = handlers['ft-pdf:click'];
assert(pdfFn, 'PDF button was never bound');
pdfFn();
assert(lastBlob, 'PDF produced no blob');
const pdf = Buffer.concat(lastBlob.parts.map((p) =>
  typeof p === 'string' ? Buffer.from(p, 'binary') : Buffer.from(p)));
assert.strictEqual(lastBlob.type, 'application/pdf');
assert.strictEqual(pdf.subarray(0, 8).toString('binary'), '%PDF-1.4');
const startxref = /startxref\s+(\d+)/.exec(pdf.toString('binary'));
assert(startxref, 'PDF has no startxref');
const off = Number(startxref[1]);
assert.strictEqual(pdf.subarray(off, off + 4).toString('binary'), 'xref');
const tail = pdf.subarray(off).toString('binary');
const count = Number(/^xref\n0 (\d+)\n/.exec(tail)[1]);
const lines = tail.split('\n');
const offsets = lines
  .filter((l) => /^\d{10} 00000 n/.test(l)).map((l) => Number(l.slice(0, 10)));
assert.strictEqual(offsets.length, count - 1, 'xref entry count mismatch');
offsets.forEach((p, i) => {
  assert(new RegExp('^' + (i + 1) + ' 0 obj').test(pdf.subarray(p, p + 20).toString('binary')),
    'xref offset ' + p + ' does not point at object ' + (i + 1));
});
assert(/%%EOF\s*$/.test(tail), 'PDF has no EOF marker');
console.log(`PASS  PDF: ${count - 1} objects, ${pdf.length} bytes, all xref offsets valid`);

/* ---- ICS: editable time inputs, button glyphs, midnight rollover ---- */
lastBlob = null;
const icsFn = handlers['ft-ics:click'];
assert(icsFn, 'ICS button was never bound');
icsFn();
assert(lastBlob, 'ICS produced no blob');
const ics = lastBlob.parts.join('');
assert.strictEqual(lastBlob.type, 'text/calendar;charset=utf-8');
assert(ics.startsWith('BEGIN:VCALENDAR') && ics.trimEnd().endsWith('END:VCALENDAR'));
assert.strictEqual((ics.match(/BEGIN:VEVENT/g) || []).length, 3);
const starts = (ics.match(/DTSTART:(\d{8}T\d{6})/g) || []).map((s) => s.slice(8));
assert(starts.includes('20260620T090000'), 'edited 09:00 time input was lost');
assert(starts.includes('20260621T001500'), 'post-midnight event did not roll to the next day');
const summaries = (ics.match(/SUMMARY:([^\r\n]*)/g) || []).map((s) => s.slice(8));
assert(!summaries.some((s) => s.includes('\u2191') || s.includes('\u2193')),
  'move-button glyphs leaked into a SUMMARY');
assert(ics.includes('DESCRIPTION:Responsible: Stylists'), 'who column was lost');
console.log(`PASS  ICS: 3 events, ${starts.join(', ')}, ${Buffer.byteLength(ics)} bytes`);
console.log('ALL CHECKS PASSED');
