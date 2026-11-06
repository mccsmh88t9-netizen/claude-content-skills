const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
for (const k of ['paper', '0', '1', '2', '3']) { await p.goto('http://localhost:8123/src/bake.html?k=' + k); await p.waitForFunction('window.READY === true');
  await p.screenshot({ path: `assets/${k === 'paper' ? 'paper' : 'grain' + k}.png`, omitBackground: k !== 'paper' }); }
await b.close(); })();
