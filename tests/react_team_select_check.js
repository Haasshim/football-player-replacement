// Verifies the React-based team-select tiles (hover-to-club-colors) actually
// work.
const { loadApp, wait, assert } = require('./_test_helpers');
const dom = loadApp();
const { window } = dom;

async function main() {
  await wait(500);
  const doc = window.document;

  assert(typeof window.React !== 'undefined', 'React did not load (check node_modules/react is installed)');
  assert(typeof window.ReactDOM !== 'undefined', 'ReactDOM did not load (check node_modules/react-dom is installed)');
  console.log('OK: React', window.React.version, 'and ReactDOM loaded');

  doc.querySelector('#get-started-btn').click();
  await wait(100);

  const reactGrid = doc.querySelector('#react-team-grid');
  assert(reactGrid, 'expected react-team-grid container to exist');
  await wait(200);
  const tiles = reactGrid.children[0] ? reactGrid.children[0].children : [];
  assert(tiles.length === 20, `expected 20 React-rendered team tiles, got ${tiles.length}`);
  console.log('OK: React rendered', tiles.length, 'team tiles');

  // React synthesizes onMouseEnter/onMouseLeave from native mouseover/mouseout
  // (mouseenter/mouseleave don't bubble, so React's delegation model ignores them)
  const firstTile = tiles[0];
  const bgBefore = firstTile.style.background;
  firstTile.dispatchEvent(new window.MouseEvent('mouseover', { bubbles: true }));
  await wait(100);
  const bgAfterHover = firstTile.style.background;
  assert(bgAfterHover && bgAfterHover !== bgBefore, `expected background to change on hover, got: ${bgAfterHover}`);
  console.log('OK: tile background changes to club color on hover:', bgAfterHover);

  firstTile.dispatchEvent(new window.MouseEvent('mouseout', { bubbles: true }));
  await wait(100);
  assert(firstTile.style.background === bgBefore, 'expected background to revert on mouseleave');
  console.log('OK: tile background reverts on mouseleave');

  // keyboard accessibility
  assert(firstTile.getAttribute('tabindex') === '0', 'expected tiles to be keyboard-focusable');
  assert(firstTile.getAttribute('role') === 'button', 'expected tiles to have role="button"');
  firstTile.click();
  await wait(100);
  assert(doc.querySelectorAll('.token').length > 0, 'expected clicking/activating a React tile to navigate to the squad page');
  console.log('OK: tiles are keyboard-accessible and activating one navigates to the squad page');

  console.log('\nREACT TEAM SELECT CHECKS PASSED');
}

main().catch((e) => { console.error('ERROR:', e); process.exit(1); });
