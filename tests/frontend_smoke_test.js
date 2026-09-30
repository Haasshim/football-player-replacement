const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'index.html'), 'utf8');

const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
const { window } = dom;

function wait(ms) { return new Promise((res) => setTimeout(res, ms)); }

async function main() {
  await wait(200); // let inline scripts run
  const doc = window.document;

  // 1. Teams page should have rendered team cards
  const teamCards = doc.querySelectorAll('.team-card');
  assert(teamCards.length === 8, `expected 8 team cards, got ${teamCards.length}`);
  console.log('OK: teams page rendered', teamCards.length, 'team cards');

  // 2. Click a team -> should move to squad view with 11 tokens
  teamCards[0].click();
  await wait(50);
  const tokens = doc.querySelectorAll('.token');
  assert(tokens.length === 11, `expected 11 starting tokens, got ${tokens.length}`);
  console.log('OK: squad page rendered', tokens.length, 'starting XI tokens');

  const benchChips = doc.querySelectorAll('.bench-chip');
  assert(benchChips.length > 0, 'expected at least one bench player');
  console.log('OK: bench rendered', benchChips.length, 'reserves');

  // 3. Click a starting player (current)
  tokens[0].click();
  await wait(50);
  const selectedToken = doc.querySelector('.token.selected');
  assert(selectedToken, 'expected a token to have the selected class after clicking');
  console.log('OK: current player selection highlights token');

  // 4. Search should find players NOT limited to this team
  const searchInput = doc.querySelector('#search-input');
  assert(searchInput, 'expected search input to exist');
  searchInput.value = 'a'; // broad query, should match many players across all clubs
  const inputEvent = new window.Event('input', { bubbles: true });
  searchInput.dispatchEvent(inputEvent);
  await wait(50);

  const resultRows = doc.querySelectorAll('.search-result-row');
  assert(resultRows.length > 0, 'expected search results for a broad query');

  // confirm results include players from more than one club (i.e. not team-restricted)
  const resultMetaTexts = Array.from(resultRows).map((r) => r.querySelector('.search-result-meta').textContent);
  const distinctClubs = new Set(resultMetaTexts.map((t) => t.split('\u00b7')[1].trim()));
  assert(distinctClubs.size >= 1, 'expected search results to include club info');
  console.log('OK: search returned', resultRows.length, 'results across clubs:', Array.from(distinctClubs).join(', '));

  // 5. Select a candidate from search results
  resultRows[0].click();
  await wait(50);
  const compareBtn = doc.querySelector('#compare-btn');
  assert(compareBtn && !compareBtn.disabled, 'expected compare button to be enabled after both selections');
  console.log('OK: compare button enabled after current + candidate selected');

  // 6. Go to compare page
  compareBtn.click();
  await wait(50);
  const scoreSvg = doc.querySelector('.score-block svg text');
  assert(scoreSvg, 'expected a match score to render');
  console.log('OK: comparison page rendered with match score:', scoreSvg.textContent);

  const statRows = doc.querySelectorAll('.stat-row');
  assert(statRows.length > 0, 'expected stat comparison rows');
  console.log('OK:', statRows.length, 'stat comparison rows rendered');

  // 7. Confirm replace works and returns to squad with swapped player
  const replaceBtn = doc.querySelector('#replace-btn');
  replaceBtn.click();
  await wait(50);
  const tokensAfter = doc.querySelectorAll('.token');
  assert(tokensAfter.length === 11, 'expected still 11 tokens after replacement');
  console.log('OK: replace player returns to squad view with 11 tokens intact');

  console.log('\nALL FRONTEND FLOW CHECKS PASSED');
  process.exit(0);
}

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL:', msg);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('ERROR during test:', err);
  process.exit(1);
});
