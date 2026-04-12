const puppeteer = require('puppeteer-core');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--disable-dbus', '--single-process'],
    headless: 'new',
    protocolTimeout: 30000,
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 1000, deviceScaleFactor: 2 });

  const htmlPath = path.resolve(__dirname, 'arch_diagram.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 2000));

  const root = await page.$('#root');
  const box = await root.boundingBox();

  await page.screenshot({
    path: path.resolve(__dirname, 'fig_architecture_new.png'),
    clip: { x: 0, y: 0, width: box.width, height: box.height + 20 },
    type: 'png',
  });

  await browser.close();
  console.log('Screenshot saved!');
})();
