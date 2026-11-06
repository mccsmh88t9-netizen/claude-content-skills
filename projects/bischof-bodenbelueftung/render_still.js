const { chromium } = require('playwright');
(async () => {
  const [,, page_, out] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => console.log('console:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('http://localhost:8123/src/' + page_); await p.waitForFunction('window.READY === true', null, { timeout: 30000 });
  await p.screenshot({ path: out }); await b.close();
})();
