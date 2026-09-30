const fs = require('fs');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(require('path').join(__dirname, '..', 'frontend', 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
const { window } = dom;

function wait(ms) { return new Promise((res) => setTimeout(res, ms)); }

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exit(1); }
}

async function main() {
  await wait(200);
  const doc = window.document;

  // Navigate: home -> teams -> pick a team -> find a GK starter -> search for another GK -> compare
  doc.querySelector('#get-started-btn').click();
  await wait(50);

  // find a team whose starting GK is easy to find, then search for ANY other GK
  const teamCards = doc.querySelectorAll('.team-card');
  let gkToken = null, teamIndex = 0;
  for (; teamIndex < teamCards.length; teamIndex++) {
    teamCards[teamIndex].click();
    await wait(30);
    const tokens = Array.from(doc.querySelectorAll('.token'));
    // GK is always the last pitch row (single token) per ROWS ordering
    gkToken = tokens[tokens.length - 1];
    if (gkToken) break;
  }
  assert(gkToken, 'expected to find a GK token on some team');
  gkToken.click();
  await wait(30);
  assert(doc.querySelector('.token.selected'), 'expected GK token to be selected');

  // search for "g" and find a search result tagged GK
  const searchInput = doc.querySelector('#search-input');
  searchInput.value = 'a';
  searchInput.dispatchEvent(new window.Event('input', { bubbles: true }));
  await wait(50);
  let rows = Array.from(doc.querySelectorAll('.search-result-row'));
  let gkRow = rows.find((r) => r.querySelector('.search-result-meta').textContent.startsWith('GK'));
  // widen the search if none found in first batch
  if (!gkRow) {
    searchInput.value = 'e';
    searchInput.dispatchEvent(new window.Event('input', { bubbles: true }));
    await wait(50);
    rows = Array.from(doc.querySelectorAll('.search-result-row'));
    gkRow = rows.find((r) => r.querySelector('.search-result-meta').textContent.startsWith('GK'));
  }
  assert(gkRow, 'expected to find a GK candidate in search results');
  gkRow.click();
  await wait(30);

  doc.querySelector('#compare-btn').click();
  await wait(50);

  const radarSvg = doc.querySelector('.radar-wrap svg');
  assert(radarSvg, 'expected a radar chart to render for a GK vs GK comparison');
  const polygons = doc.querySelectorAll('.radar-wrap polygon');
  assert(polygons.length >= 6, `expected radar polygons for GK comparison, got ${polygons.length}`);
  const labels = Array.from(doc.querySelectorAll('.radar-wrap text')).map((el) => el.textContent);
  assert(labels.length >= 3, 'expected axis labels on the GK radar');
  console.log('OK: GK vs GK radar renders with', polygons.length, 'polygons and labels:', labels.join(', '));

  const scoreSvgText = doc.querySelector('.score-block svg text');
  assert(scoreSvgText && !isNaN(parseFloat(scoreSvgText.textContent)), 'expected a valid numeric match score for GK vs GK');
  console.log('OK: GK vs GK match score is valid:', scoreSvgText.textContent);

  console.log('\nGK EDGE CASE CHECKS PASSED');
}

main().catch((e) => { console.error('ERROR:', e); process.exit(1); });
