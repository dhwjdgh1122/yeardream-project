// Run the actual inline UI script with a minimal DOM and a mocked API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../frontend/static/index.html'), 'utf8');
const elements = {};
for (const id of ['url', 'output', 'status', 'techniqueFilter', 'analyze', 'collectionMode', 'download']) {
  elements[id] = { value: '', textContent: '', disabled: false, handlers: {},
    addEventListener(event, callback) { this.handlers[event] = callback; } };
}
elements.url.value = 'https://example.com';
elements.techniqueFilter.value = 'ALL';
elements.collectionMode.value = 'static';
elements.download.disabled = true;
const response = {
  url: elements.url.value, page_title: 'Fixture', crawled_pages: [elements.url.value],
  findings: [
    { technique: 'JAMO', selector: 'div#a', location: 'div#a', evidence: 'A' },
    { technique: 'TRANSPARENT', selector: 'div#b', location: 'div#b', evidence: 'B' },
  ],
};
response.result_json = { meta: { entry_url: response.url }, findings: [
  { id: 'finding-1', technique: 'JAMO', evidence_text: '한글 근거', is_violation: true },
  { id: 'finding-2', technique: 'TRANSPARENT', evidence_text: 'B', is_violation: true },
] };
let fail = false;
const downloads = [];
const objectUrls = new Map();
const cleanup = [];
const context = vm.createContext({
  Blob,
  URL: {
    createObjectURL(blob) { const url = `blob:test-${objectUrls.size}`; objectUrls.set(url, blob); return url; },
    revokeObjectURL(url) { assert.ok(objectUrls.delete(url)); },
  },
  setTimeout(callback) { cleanup.push(callback); },
  document: {
    getElementById: id => elements[id],
    body: { appendChild(link) { link.attached = true; } },
    createElement(tag) {
      assert.equal(tag, 'a');
      return {
        click() { assert.ok(this.attached); downloads.push({ filename: this.download, blob: objectUrls.get(this.href) }); },
        remove() { this.attached = false; },
      };
    },
  },
  fetch: async (url, options) => {
    assert.equal(url, '/api/analyze');
    assert.equal(options.method, 'POST');
    assert.equal(elements.analyze.disabled, true);
    assert.equal(elements.collectionMode.disabled, true);
    assert.equal(elements.download.disabled, true);
    assert.equal(JSON.parse(options.body).collection_mode, elements.collectionMode.value);
    if (fail) throw new Error('Fixture failure');
    return { ok: true, json: async () => response };
  },
});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);

async function run() {
  elements.download.handlers.click();
  assert.equal(downloads.length, 0);
  await elements.analyze.handlers.click();
  assert.equal(elements.download.disabled, false);
  assert.equal(elements.analyze.disabled, false);
  assert.equal(JSON.parse(elements.output.textContent).totalFindings, 2);
  for (const [filter, count] of [['JAMO', 1], ['OFFSCREEN', 0], ['TRANSPARENT', 1], ['ALL', 2]]) {
    elements.techniqueFilter.value = filter;
    elements.techniqueFilter.handlers.change();
    const data = JSON.parse(elements.output.textContent);
    assert.equal(data.totalFindings, count);
    assert.equal(data.totalPages, 1);
    if (count) assert.ok(data.findings[0].evidence);
  }
  elements.techniqueFilter.value = 'OFFSCREEN';
  elements.techniqueFilter.handlers.change();
  elements.download.handlers.click();
  assert.equal(downloads[0].filename, 'result.json');
  assert.deepEqual(JSON.parse(await downloads[0].blob.text()), response.result_json);
  assert.equal(downloads[0].blob.type, 'application/json;charset=utf-8');
  assert.equal(Buffer.from(await downloads[0].blob.arrayBuffer()).subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])), false);
  cleanup.splice(0).forEach(callback => callback());
  assert.equal(objectUrls.size, 0);
  response.warnings = ['Some frames could not be analyzed'];
  elements.collectionMode.value = 'browser';
  await elements.analyze.handlers.click();
  assert.deepEqual(JSON.parse(elements.output.textContent).warnings, response.warnings);
  fail = true;
  await elements.analyze.handlers.click();
  assert.equal(elements.analyze.disabled, false);
  assert.equal(elements.collectionMode.disabled, false);
  assert.equal(elements.output.textContent, 'Fixture failure');
  assert.equal(elements.download.disabled, true);
  elements.download.handlers.click();
  assert.equal(downloads.length, 1);
  elements.techniqueFilter.handlers.change();
  assert.equal(elements.output.textContent, 'Fixture failure');
  fail = false;
  response.findings = [];
  response.result_json = { meta: { entry_url: response.url }, findings: [] };
  await elements.analyze.handlers.click();
  elements.download.handlers.click();
  assert.deepEqual(JSON.parse(await downloads[1].blob.text()), response.result_json);
  cleanup.splice(0).forEach(callback => callback());
  elements.url.value = '  ';
  await elements.analyze.handlers.click();
  assert.equal(elements.download.disabled, true);
  elements.download.handlers.click();
  assert.equal(downloads.length, 2);
  assert.equal(objectUrls.size, 0);
  console.log('Frontend checks passed: API, modes, filters, partial results, failure reset, full JSON downloads, empty results, UTF-8, URL cleanup.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
