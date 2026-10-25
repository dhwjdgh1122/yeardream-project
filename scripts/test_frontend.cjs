// Run the actual inline UI script with a minimal DOM and a mocked API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../frontend/static/index.html'), 'utf8');
const elements = {};
for (const id of ['url', 'output', 'status', 'techniqueFilter', 'analyze', 'collectionMode', 'download', 'downloadContent', 'downloadExtra',
  'summary', 'warnings', 'findingCards', 'contentCards', 'findingHeading', 'contentHeading', 'rawDetails',
  'coverageSummary', 'coverageDetails', 'coverageDocuments']) {
  elements[id] = { value: '', textContent: '', disabled: false, handlers: {},
    children: [], appendChild(node) { this.children.push(node); }, replaceChildren() { this.children = []; },
    addEventListener(event, callback) { this.handlers[event] = callback; } };
}
elements.url.value = 'https://example.com';
elements.techniqueFilter.value = 'ALL';
elements.collectionMode.value = 'static';
elements.download.disabled = true;
elements.downloadContent.disabled = true;
elements.downloadExtra.disabled = true;
const response = {
  url: elements.url.value, page_title: 'Fixture', crawled_pages: [elements.url.value],
  findings: [
    { technique: 'JAMO', selector: 'div#a', location: 'div#a', evidence: 'A', source_text: '<img src=x onerror=alert(1)>',
      confidence: 0.99, submission_status: 'included',
      submission_reason: 'Matched promotion', submission_categories: ['GAMBLING'] },
    { technique: 'TRANSPARENT', selector: 'div#b', location: 'div#b', evidence: 'B', submission_status: 'needs_review',
      submission_reason: 'No relevant promotion', submission_categories: [] },
  ],
  content_candidates: [{ category: 'GAMBLING', location: 'p#ad', techniques: [], review_status: 'needs_review' }],
  submission_policy_version: 'feature-content-policy-v1',
};
response.result_json = { meta: { entry_url: response.url }, findings: [
  { id: 'finding-1', technique: 'JAMO', evidence_text: '한글 근거', is_violation: true },
] };
response.result_extra_json = { meta: { topic: 'TOPIC', entry_url: response.url }, findings: [
  { id: 'extra-1', technique: 'ETC', extra_finding: 'GAMBLING_PROMOTION_CANDIDATE', evidence_text: '가입 원문' },
] };
response.coverage = {
  attempted_documents: 2, collected_documents: 2, analyzed_documents: 1, failed_documents: 0,
  unvisited_known_urls: 1, limits: { max_documents: 8, max_depth: 2, total_timeout_sec: 60 },
  documents: [{ url: response.url, requested_url: response.url, depth: 0, frame_path: [], status: 'analyzed', reason: '' },
    { url: response.url + '/next', requested_url: response.url + '/next', depth: 1, frame_path: [], status: 'not_analyzed', reason: '' }],
  unvisited_links: [{ url: '<img src=x onerror=alert(1)>', source_url: response.url, reason: 'max_pages' }],
  excluded_frames: [{ source_url: response.url, location: 'iframe#external', reason: 'unsupported_or_external_src' }]
};
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
      return {
        tag, textContent: '', children: [], appendChild(node) { this.children.push(node); },
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
    assert.equal(elements.downloadContent.disabled, true);
    assert.equal(elements.downloadExtra.disabled, true);
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
  assert.equal(JSON.parse(elements.output.textContent).totalSubmittedFindings, 1);
  assert.equal(JSON.parse(elements.output.textContent).totalNeedsReviewFindings, 1);
  assert.equal(JSON.parse(elements.output.textContent).submissionPolicyVersion, 'feature-content-policy-v1');
  assert.equal(elements.findingCards.children.length, 2);
  assert.equal(elements.findingCards.children[0].children[1].textContent, response.findings[0].source_text);
  assert.ok(elements.findingCards.children[0].children[0].textContent.includes('제출 후보'));
  assert.ok(elements.findingCards.children[1].children[0].textContent.includes('검토 필요'));
  assert.equal(elements.rawDetails.open, false);
  assert.ok(elements.coverageSummary.textContent.includes('탐지 완료 1개'));
  assert.ok(elements.coverageSummary.textContent.includes('미방문한 URL 1개'));
  assert.ok(elements.coverageDocuments.children.some(node => node.textContent.includes('<img src=x onerror=alert(1)>')));
  assert.ok(!elements.output.textContent.includes('confidence'));
  assert.ok(elements.summary.textContent.includes('0건은 광고 부재를 뜻하지 않습니다'));
  for (const [filter, count] of [['JAMO', 1], ['OFFSCREEN', 0], ['TRANSPARENT', 1], ['ALL', 2]]) {
    elements.techniqueFilter.value = filter;
    elements.techniqueFilter.handlers.change();
    const data = JSON.parse(elements.output.textContent);
    assert.equal(data.totalFindings, count);
    assert.equal(data.totalPages, 1);
    if (count) assert.ok(data.findings[0].evidence);
  }
  elements.techniqueFilter.value = 'GAMBLING';
  elements.techniqueFilter.handlers.change();
  assert.equal(JSON.parse(elements.output.textContent).totalFindings, 0);
  assert.equal(JSON.parse(elements.output.textContent).totalContentCandidates, 1);
  elements.techniqueFilter.value = 'OFFSCREEN';
  elements.techniqueFilter.handlers.change();
  elements.download.handlers.click();
  assert.equal(downloads[0].filename, 'result.json');
  assert.deepEqual(JSON.parse(await downloads[0].blob.text()), response.result_json);
  assert.equal(downloads[0].blob.type, 'application/json;charset=utf-8');
  assert.equal(Buffer.from(await downloads[0].blob.arrayBuffer()).subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])), false);
  cleanup.splice(0).forEach(callback => callback());
  assert.equal(objectUrls.size, 0);
  // Use a separate download then remove it from the shared checks' history.
  elements.downloadExtra.handlers.click();
  const extraDownload = downloads.pop();
  assert.equal(extraDownload.filename, 'result_extra.json');
  assert.deepEqual(JSON.parse(await extraDownload.blob.text()), response.result_extra_json);
  cleanup.splice(0).forEach(callback => callback());
  elements.downloadContent.handlers.click();
  assert.equal(downloads[1].filename, 'content-candidates.json');
  const contentReport = JSON.parse(await downloads[1].blob.text());
  assert.deepEqual(contentReport.candidates, response.content_candidates);
  assert.equal(contentReport.purpose, 'content_candidate_review');
  cleanup.splice(0).forEach(callback => callback());
  response.warnings = ['Some frames could not be analyzed'];
  elements.collectionMode.value = 'browser';
  await elements.analyze.handlers.click();
  assert.deepEqual(JSON.parse(elements.output.textContent).warnings, response.warnings);
  assert.equal(elements.warnings.children[0].textContent, response.warnings[0]);
  assert.ok(elements.status.textContent.includes('일부 범위 미분석'));
  response.warnings = ['분석 이력을 저장하지 못했습니다. 현재 결과와 JSON 다운로드는 사용할 수 있습니다.'];
  await elements.analyze.handlers.click();
  assert.ok(!elements.status.textContent.includes('일부 범위 미분석'));
  assert.equal(elements.warnings.children[0].textContent, response.warnings[0]);
  assert.equal(elements.download.disabled, false);
  fail = true;
  await elements.analyze.handlers.click();
  assert.equal(elements.analyze.disabled, false);
  assert.equal(elements.collectionMode.disabled, false);
  assert.equal(elements.output.textContent, 'Fixture failure');
  assert.ok(elements.summary.textContent.includes('Fixture failure'));
  assert.equal(elements.findingCards.children.length, 0);
  assert.equal(elements.contentCards.children.length, 0);
  assert.equal(elements.warnings.children.length, 0);
  assert.equal(elements.coverageDocuments.children.length, 0);
  assert.equal(elements.download.disabled, true);
  assert.equal(elements.downloadContent.disabled, true);
  assert.equal(elements.downloadExtra.disabled, true);
  elements.downloadExtra.handlers.click();
  elements.download.handlers.click();
  elements.downloadContent.handlers.click();
  assert.equal(downloads.length, 2);
  elements.techniqueFilter.handlers.change();
  assert.equal(elements.output.textContent, 'Fixture failure');
  fail = false;
  response.findings = [];
  response.result_json = { meta: { entry_url: response.url }, findings: [] };
  response.result_extra_json = { meta: { topic: 'TOPIC', entry_url: response.url }, findings: [] };
  await elements.analyze.handlers.click();
  elements.downloadExtra.handlers.click();
  assert.deepEqual(JSON.parse(await downloads.pop().blob.text()), response.result_extra_json);
  cleanup.splice(0).forEach(callback => callback());
  elements.download.handlers.click();
  assert.deepEqual(JSON.parse(await downloads[2].blob.text()), response.result_json);
  cleanup.splice(0).forEach(callback => callback());
  elements.url.value = '  ';
  await elements.analyze.handlers.click();
  assert.equal(elements.download.disabled, true);
  assert.equal(elements.downloadExtra.disabled, true);
  elements.download.handlers.click();
  assert.equal(downloads.length, 3);
  assert.equal(objectUrls.size, 0);
  console.log('Frontend checks passed: API, modes, filters, partial results, failure reset, full JSON downloads, empty results, UTF-8, URL cleanup.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
