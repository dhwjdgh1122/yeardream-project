// Run the actual inline UI script with a minimal DOM and a mocked API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../frontend/static/index.html'), 'utf8');
const elements = {};
for (const id of ['url', 'output', 'status', 'techniqueFilter', 'analyze']) {
  elements[id] = { value: '', textContent: '', disabled: false, handlers: {},
    addEventListener(event, callback) { this.handlers[event] = callback; } };
}
elements.url.value = 'https://example.com';
elements.techniqueFilter.value = 'ALL';
const response = {
  url: elements.url.value, page_title: 'Fixture', crawled_pages: [elements.url.value],
  findings: [
    { technique: 'JAMO', selector: 'div#a', location: 'div#a', evidence: 'A' },
    { technique: 'TRANSPARENT', selector: 'div#b', location: 'div#b', evidence: 'B' },
  ],
};
let fail = false;
const context = vm.createContext({
  document: { getElementById: id => elements[id] },
  fetch: async (url, options) => {
    assert.equal(url, '/api/analyze');
    assert.equal(options.method, 'POST');
    assert.equal(elements.analyze.disabled, true);
    if (fail) throw new Error('Fixture failure');
    return { ok: true, json: async () => response };
  },
});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);

async function run() {
  await elements.analyze.handlers.click();
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
  response.warnings = ['Some frames could not be analyzed'];
  await elements.analyze.handlers.click();
  assert.deepEqual(JSON.parse(elements.output.textContent).warnings, response.warnings);
  fail = true;
  await elements.analyze.handlers.click();
  assert.equal(elements.analyze.disabled, false);
  assert.equal(elements.output.textContent, 'Fixture failure');
  elements.techniqueFilter.handlers.change();
  assert.equal(elements.output.textContent, 'Fixture failure');
  console.log('Frontend checks passed: API path, filters, restore all, evidence, partial results, failure reset.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
