// node render_frames.js <start> <end> <step> <outdir> [workers]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [,, s0, s1, stepS, out, wk = '4'] = process.argv;
  const start = parseFloat(s0), end = parseFloat(s1), step = parseFloat(stepS), workers = parseInt(wk);
  fs.mkdirSync(out, { recursive: true });
  const times = []; for (let f = Math.round(start * 30); f < Math.round(end * 30); f += Math.round(step * 30)) times.push(f);
  let idx = 0; const t0 = Date.now();
  await Promise.all([...Array(workers)].map(async () => {
    const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    p.on('pageerror', e => console.log('ERR', e.message));
    await p.goto('http://localhost:' + (process.env.PORT || 8124) + '/src/video.html'); await p.waitForFunction('window.READY === true', null, { timeout: 60000 });
    while (idx < times.length) {
      const f = times[idx++]; if (fs.existsSync(`${out}/f${String(f).padStart(5, '0')}.png`)) continue;
      await p.evaluate(t => window.renderAt(t), f / 30);
      await p.screenshot({ path: `${out}/f${String(f).padStart(5, '0')}.png` });
      if (f % 60 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    await b.close();
  })); console.log('done', times.length, ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
