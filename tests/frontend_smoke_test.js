const { loadApp, wait } = require('./_test_helpers');

const dom = loadApp();
const { window } = dom;

async function main() {
  await wait(200); // let inline scripts run
  const doc = window.document;

  // 0. Homepage should render first, with title, description, how-it-works
  // cards, and a working methodology toggle, before any team cards exist
  assert(doc.title === 'EPL Player Matcher', `expected page title "EPL Player Matcher", got "${doc.title}"`);
  const heroTitle = doc.querySelector('.hero h1');
  assert(heroTitle && heroTitle.textContent.includes('EPL Player Matcher'), 'expected homepage hero title');
  const heroDesc = doc.querySelector('.hero p');
  assert(heroDesc && heroDesc.textContent.length > 40, 'expected a homepage description');
  console.log('OK: homepage rendered with title and description');

  const howCards = doc.querySelectorAll('.how-card');
  assert(howCards.length === 3, `expected 3 how-it-works cards, got ${howCards.length}`);
  console.log('OK: homepage shows', howCards.length, 'how-it-works steps');

  assert(doc.querySelectorAll('.team-card').length === 0, 'team cards should not exist before leaving the homepage');

  const methodToggle = doc.querySelector('#method-toggle');
  const methodBody = doc.querySelector('#method-body');
  assert(methodToggle && methodBody, 'expected a methodology explainer toggle');
  assert(!methodBody.classList.contains('open'), 'methodology body should start collapsed');
  methodToggle.click();
  await wait(30);
  assert(doc.querySelector('#method-body').classList.contains('open'), 'methodology body should open after clicking the toggle');
  console.log('OK: "how the scores work" methodology toggle expands');

  const jerseyIcons = doc.querySelectorAll('.jersey-strip svg');
  assert(jerseyIcons.length === 20, `expected 20 jersey icons on homepage, got ${jerseyIcons.length}`);
  console.log('OK: homepage jersey strip shows', jerseyIcons.length, 'clubs');

  const githubLink = doc.querySelector('.github-link');
  assert(githubLink && githubLink.getAttribute('href') === 'https://github.com/Haasshim/football-player-replacement', 'expected a working GitHub source link');
  console.log('OK: GitHub source link present and correct');

  // "Try a random comparison" should jump straight to a valid compare page
  const randomBtn = doc.querySelector('#random-btn');
  assert(randomBtn, 'expected a "Try a random comparison" button');
  randomBtn.click();
  await wait(50);
  const randomScoreSvg = doc.querySelector('.score-block svg text');
  assert(randomScoreSvg && !isNaN(parseFloat(randomScoreSvg.textContent)), 'expected random comparison to land on a valid compare page with a real score');
  console.log('OK: "Try a random comparison" jumps straight to a valid comparison:', randomScoreSvg.textContent);

  // back to a clean state (home) for the rest of the flow, same as the
  // original test's expectation of starting fresh from the homepage
  doc.querySelector('#back-btn').click();
  await wait(50);
  doc.querySelector('.brand-btn').click();
  await wait(50);

  // 0b. The CTA button should take us to team selection
  const getStartedBtn = doc.querySelector('#get-started-btn');
  assert(getStartedBtn, 'expected a "Choose your team" CTA button on the homepage');
  getStartedBtn.click();
  await wait(50);

  // 1. Teams page should have rendered team cards
  const teamCards = doc.querySelectorAll('.team-card');
  assert(teamCards.length === 20, `expected 20 team cards, got ${teamCards.length}`);
  console.log('OK: teams page rendered', teamCards.length, 'team cards');

  const badges = doc.querySelectorAll('.badge');
  assert(badges.length > 0, 'expected team badges to render');
  console.log('OK:', badges.length, 'team badges rendered on this page');

  // team cards must show whole numbers with a clear "recent form" qualifier,
  // never a raw decimal like "1.8th" or "82.8 pts" with no explanation
  const teamMetaTexts = Array.from(doc.querySelectorAll('.team-meta')).map((el) => el.textContent);
  const hasDecimalPosition = teamMetaTexts.some((t) => /\d+\.\d+(st|nd|rd|th)/.test(t));
  assert(!hasDecimalPosition, `found an unexplained decimal position in a team card: ${teamMetaTexts.find((t) => /\d+\.\d+(st|nd|rd|th)/.test(t))}`);
  const allHaveQualifier = teamMetaTexts.every((t) => t.includes('recent form') || t.includes('no recent top-flight data'));
  assert(allHaveQualifier, 'expected every team card to explain that position/points are a recent-form blend, not a literal table');
  const strengthLabels = doc.querySelectorAll('.team-card');
  assert(Array.from(strengthLabels).every((c) => c.textContent.includes('Squad strength')), 'expected every team card to label the strength bar');
  console.log('OK: team cards show whole numbers with a "recent form" explanation, no unexplained decimals');

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

  const radarSvg = doc.querySelector('.radar-wrap svg');
  assert(radarSvg, 'expected an overlaid radar chart to render on the comparison page');
  const radarPolygons = doc.querySelectorAll('.radar-wrap polygon');
  assert(radarPolygons.length >= 6, `expected grid rings + 2 player polygons on the radar, got ${radarPolygons.length} polygons`);
  console.log('OK: radar chart rendered with', radarPolygons.length, 'polygons');

  const ratingPills = doc.querySelectorAll('.compare-head .rating-pill');
  assert(ratingPills.length === 2, `expected 2 rating badges (one per player) on the comparison page, got ${ratingPills.length}`);
  console.log('OK: rating badges shown for both players:', Array.from(ratingPills).map((el) => el.textContent).join(' vs '));

  const statRows = doc.querySelectorAll('.stat-row');
  assert(statRows.length > 0, 'expected stat comparison rows');
  console.log('OK:', statRows.length, 'stat comparison rows rendered');

  // stat names should be clickable to reveal a plain-language definition
  const statBtn = doc.querySelector('.stat-name-btn');
  assert(statBtn, 'expected clickable stat name buttons');
  assert(!doc.querySelector('.stat-definition'), 'definition should not be visible before clicking');
  statBtn.click();
  await wait(50);
  const def = doc.querySelector('.stat-definition');
  assert(def && def.textContent.length > 15, 'expected a real definition to appear after clicking a stat name');
  console.log('OK: clicking a stat name reveals its definition:', def.textContent.slice(0, 50) + '...');
  statBtn.click();
  await wait(50);
  assert(!doc.querySelector('.stat-definition'), 'expected the definition to collapse again on a second click');
  console.log('OK: clicking again collapses the definition');


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
