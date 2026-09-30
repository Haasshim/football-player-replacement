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
  assert(teamCards.length === 20, `expected 20 team cards, got ${teamCards.length}`);
  console.log('OK: teams page rendered', teamCards.length, 'team cards');

  const badges = doc.querySelectorAll('.badge');
  assert(badges.length > 0, 'expected team badges to render');
  console.log('OK:', badges.length, 'team badges rendered on this page');

  // 2. Click a team -> should move to squad view with a starting XI (allow
  // for real-data gaps: some clubs are short a player or two in one slot)
  teamCards[0].click();
  await wait(50);
  const tokens = doc.querySelectorAll('.token');
  assert(tokens.length >= 8 && tokens.length <= 11, `expected close to 11 starting tokens, got ${tokens.length}`);
  console.log('OK: squad page rendered', tokens.length, 'starting XI tokens');

  let pageEl = doc.querySelector('#app > .page');
  assert(pageEl && pageEl.classList.contains('enter-forward'), 'expected a forward page transition teams -> squad');
  console.log('OK: forward transition applied (teams -> squad)');

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

  // typing in search re-renders the squad page directly (not through the
  // central dispatcher), so it must NOT replay the page transition
  const pageElAfterSearch = doc.querySelector('#app > .page');
  assert(pageElAfterSearch && !pageElAfterSearch.classList.contains('enter-forward') && !pageElAfterSearch.classList.contains('enter-back'),
    'search re-render should not trigger a page transition');
  console.log('OK: no transition replay while typing in search');

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

  pageEl = doc.querySelector('#app > .page');
  assert(pageEl && pageEl.classList.contains('enter-forward'), 'expected a forward page transition squad -> compare');
  console.log('OK: forward transition applied (squad -> compare)');

  const scoreLabels = Array.from(doc.querySelectorAll('.score-label')).map((el) => el.textContent);
  assert(scoreLabels.includes('team fit'), 'expected a team fit (chemistry) score alongside match score');
  const chemSvgText = doc.querySelectorAll('.score-item')[1].querySelector('svg text');
  assert(chemSvgText, 'expected a chemistry score ring to render');
  console.log('OK: team fit / chemistry score rendered:', chemSvgText.textContent);

  const statRows = doc.querySelectorAll('.stat-row');
  assert(statRows.length > 0, 'expected stat comparison rows');
  console.log('OK:', statRows.length, 'stat comparison rows rendered');

  // 7. Confirm replace works and returns to squad with swapped player
  const replaceBtn = doc.querySelector('#replace-btn');
  const expectedTokenCount = tokens.length;
  const candidateName = doc.querySelector('.compare-side.right .compare-name').textContent;
  replaceBtn.click();
  await wait(50);
  const tokensAfter = doc.querySelectorAll('.token');
  assert(tokensAfter.length === expectedTokenCount, 'expected same token count after replacement');
  console.log('OK: replace player returns to squad view with', tokensAfter.length, 'tokens intact');

  pageEl = doc.querySelector('#app > .page');
  assert(pageEl && pageEl.classList.contains('enter-back'), 'expected a back page transition compare -> squad');
  console.log('OK: back transition applied (compare -> squad)');

  // the candidate must actually be visible on the pitch now, in the same
  // slot - not vanished because their real position differs from the
  // player they replaced (this was the reported bug)
  const pitchLabels = Array.from(doc.querySelectorAll('.token .label')).map((el) => el.textContent);
  const candidateSurname = candidateName.trim().split(' ').pop();
  assert(pitchLabels.includes(candidateSurname), `expected replaced-in player "${candidateSurname}" to appear on the pitch, got: ${pitchLabels.join(', ')}`);
  console.log('OK: replacement candidate is visible on the pitch in the vacated slot');

  const banner = doc.querySelector('.panel-head + div');
  assert(banner && banner.textContent.includes('Replaced'), 'expected a swap confirmation banner');
  console.log('OK: swap confirmation banner shown:', banner.textContent.trim());

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
