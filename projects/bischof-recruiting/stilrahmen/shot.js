const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:2320,height:1920},deviceScaleFactor:1});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(800);await p.screenshot({path:process.argv[3]});await b.close()})();
