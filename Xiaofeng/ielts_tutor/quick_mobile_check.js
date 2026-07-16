// v1.0.1 移动端自适应布局验收脚本
const { chromium } = require('playwright-core');
const os = require('os');
const path = require('path');

const BIN = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-mac-arm64/chrome-headless-shell');
const URL = 'http://localhost:8767/';

async function checkViewport(browser, name, vp) {
  const ctx = await browser.newContext({ viewport: vp, isMobile: vp.width < 500, hasTouch: vp.width < 500 });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);

  const r = await page.evaluate(() => {
    const q = s => document.querySelector(s);
    const rect = s => { const e = q(s); if (!e) return null; const b = e.getBoundingClientRect(); return { x: +b.x.toFixed(0), y: +b.y.toFixed(0), w: +b.width.toFixed(0), h: +b.height.toFixed(0) }; };
    const btns = [...document.querySelectorAll('.btn, .panel-tab')].filter(b => b.offsetParent !== null)
      .map(b => ({ label: b.textContent.trim().slice(0, 10), h: +b.getBoundingClientRect().height.toFixed(0) }));
    return {
      hScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      scrollW: document.documentElement.scrollWidth,
      clientW: document.documentElement.clientWidth,
      mainDir: getComputedStyle(q('.main')).flexDirection,
      panelCollapsed: q('#rightPanel').classList.contains('collapsed'),
      panelContentHidden: getComputedStyle(q('.panel-content')).display === 'none',
      header: rect('.header'), ctrls: rect('.ctrls'),
      dialogue: rect('.dialogue-col'), panel: rect('.right-panel'),
      title: q('#appTitle').textContent,
      btns,
      overflowEls: [...document.querySelectorAll('body *')].filter(e => {
        const b = e.getBoundingClientRect();
        return b.width > 0 && b.right > document.documentElement.clientWidth + 1;
      }).slice(0, 5).map(e => e.tagName + '.' + (e.className && e.className.split ? e.className.split(' ')[0] : '')),
    };
  });
  await page.screenshot({ path: `reports/vp_${name}.png` });
  await ctx.close();
  return r;
}

(async () => {
  const browser = await chromium.launch({ executablePath: BIN });
  const mobile = await checkViewport(browser, 'mobile_390', { width: 390, height: 844 });
  const mobileSmall = await checkViewport(browser, 'mobile_360', { width: 360, height: 740 });
  const desktop = await checkViewport(browser, 'desktop_1280', { width: 1280, height: 800 });
  await browser.close();

  console.log('=== MOBILE 390x844 ===');
  console.log(JSON.stringify(mobile, null, 1));
  console.log('=== MOBILE 360x740 ===');
  console.log(JSON.stringify({ hScroll: mobileSmall.hScroll, mainDir: mobileSmall.mainDir, panelCollapsed: mobileSmall.panelCollapsed, overflowEls: mobileSmall.overflowEls, btns: mobileSmall.btns }, null, 1));
  console.log('=== DESKTOP 1280x800 ===');
  console.log(JSON.stringify({ hScroll: desktop.hScroll, mainDir: desktop.mainDir, panelCollapsed: desktop.panelCollapsed, panelW: desktop.panel && desktop.panel.w, title: desktop.title }, null, 1));

  // 断言
  const errs = [];
  if (mobile.hScroll) errs.push('mobile 390: 出现横向滚动');
  if (mobile.mainDir !== 'column') errs.push('mobile 390: main 未纵向堆叠');
  if (!mobile.panelCollapsed || !mobile.panelContentHidden) errs.push('mobile 390: 右侧面板未收起');
  if (mobile.btns.some(b => b.h < 38)) errs.push('mobile 390: 存在 <38px 触控目标: ' + JSON.stringify(mobile.btns.filter(b => b.h < 38)));
  if (mobile.overflowEls.length) errs.push('mobile 390: 元素溢出 ' + mobile.overflowEls.join(','));
  if (mobileSmall.hScroll) errs.push('mobile 360: 出现横向滚动');
  if (desktop.mainDir !== 'row') errs.push('desktop: 两栏布局被破坏');
  if (desktop.panelCollapsed) errs.push('desktop: 面板被误收起');
  if (desktop.panel && Math.abs(desktop.panel.w - 360) > 2) errs.push('desktop: 面板宽度异常 ' + desktop.panel.w);

  console.log(errs.length ? '\n❌ FAIL:\n- ' + errs.join('\n- ') : '\n✅ 全部断言通过');
  process.exit(errs.length ? 1 : 0);
})();
