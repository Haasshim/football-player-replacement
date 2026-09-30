const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
const { window } = dom;

function wait(ms) { return new Promise((res) => setTimeout(res, ms)); }
function assert(cond, msg) { if (!cond) { console.error('FAIL:', msg); process.exit(1); } }

async function main() {
  await wait(200);
  const doc = window.document;
  doc.querySelector('#get-started-btn').click();
  await wait(50);
  doc.querySelector('.team-card').click();
  await wait(50);

  const searchInput = doc.querySelector('#search-input');
  const ratings = [];
  const letters = ['a', 'e', 'i', 'o', 'r', 's', 'm'];
  for (const letter of letters) {
    searchInput.value = letter;
    searchInput.dispatchEvent(new window.Event('input', { bubbles: true }));
    await wait(30);
    const pills = Array.from(doc.querySelectorAll('.rating-pill'));
    pills.forEach((p) => {
      const v = parseFloat(p.textContent);
      if (!isNaN(v)) ratings.push(v);
    });
  }

  const unique = new Set(ratings);
  const min = Math.min(...ratings), max = Math.max(...ratings);
  const mean = ratings.reduce((a, b) => a + b, 0) / ratings.length;

  assert(ratings.length >= 15, `expected a reasonable sample of ratings, got ${ratings.length}`);
  assert(unique.size >= 8, `ratings look degenerate - only ${unique.size} distinct values across ${ratings.length} samples`);
  assert(max - min >= 3, `rating spread too narrow: min=${min} max=${max}`);
  console.log(`OK: sampled ${ratings.length} ratings, ${unique.size} distinct values, range ${min}-${max}, mean ${mean.toFixed(2)}`);
  console.log('\nRATING DISTRIBUTION CHECK PASSED');
}

main().catch((e) => { console.error('ERROR:', e); process.exit(1); });
