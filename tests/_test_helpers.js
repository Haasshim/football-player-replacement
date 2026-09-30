// Shared by every frontend test. Production loads React/ReactDOM from
// cdnjs (works fine for real users); this sandbox's test runner can't
// reach that host, so tests swap in the local npm-installed copies
// instead - same React version, same behavior, just a different URL.
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.join(__dirname, '..');

function loadApp() {
  const html = fs.readFileSync(path.join(ROOT, 'frontend', 'index.html'), 'utf8')
    .replace(
      'https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js',
      'file://' + path.join(ROOT, 'node_modules', 'react', 'umd', 'react.development.js')
    )
    .replace(
      'https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js',
      'file://' + path.join(ROOT, 'node_modules', 'react-dom', 'umd', 'react-dom.development.js')
    );

  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    resources: 'usable',
    url: 'file://' + path.join(ROOT, 'frontend', 'index.html'),
  });
  return dom;
}

function wait(ms) { return new Promise((res) => setTimeout(res, ms)); }
function assert(cond, msg) { if (!cond) { console.error('FAIL:', msg); process.exit(1); } }

module.exports = { loadApp, wait, assert };
