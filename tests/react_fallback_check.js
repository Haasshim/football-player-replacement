// Simulates the React/ReactDOM CDN scripts failing to load (blocked host,
// network blip, ad-blocker, etc.) and confirms the team-select page still
// works via its plain-HTML fallback, rather than rendering an empty grid.
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const { wait, assert } = require('./_test_helpers');

const ROOT = path.join(__dirname, '..');
// deliberately point React/ReactDOM at URLs that don't exist, so they fail
// to load exactly like a blocked CDN would
const html = fs.readFileSync(path.join(ROOT, 'frontend', 'index.html'), 'utf8')
  .replace(
    'https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js',
    'file:///nonexistent/react.js'
  )
  .replace(
    'https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js',
    'file:///nonexistent/react-dom.js'
  );

const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
const { window } = dom;

async function main() {
  await wait(300);
  const doc = window.document;

  assert(typeof window.React === 'undefined', 'test setup check: React should have failed to load');
  assert(typeof window.ReactDOM === 'undefined', 'test setup check: ReactDOM should have failed to load');

  doc.querySelector('#get-started-btn').click();
  await wait(100);

  const cards = doc.querySelectorAll('.team-card');
  assert(cards.length === 20, `expected the fallback to render 20 plain team cards, got ${cards.length}`);
  console.log('OK: fallback rendered', cards.length, 'team cards without React');

  cards[0].click();
  await wait(100);
  assert(doc.querySelectorAll('.token').length > 0, 'expected clicking a fallback card to still navigate to the squad page');
  console.log('OK: fallback cards are still clickable and navigate correctly');

  console.log('\nREACT FALLBACK CHECKS PASSED');
}

main().catch((e) => { console.error('ERROR:', e); process.exit(1); });
