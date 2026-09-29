// Optional browser QA. npm's Playwright package + a Chromium executable are required.
// They are development dependencies only; readers and builders need neither.
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_BIN ? {executablePath: process.env.CHROME_BIN} : {}),
  });
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [], requests = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("request", request => {if (/^https?:/.test(request.url())) requests.push(request.url());});
    const url = pathToFileURL(path.resolve(__dirname, "../index.html")).href;
    await page.goto(url);
    assert.equal(await page.locator(".card").count(), 60);
    assert.equal(await page.locator("#filters").isVisible(), true);
    await page.locator("#query").fill("J019");
    assert.equal(await page.locator(".card:visible").count(), 1);
    await page.locator("#query").fill("没有这个关键词987654");
    assert.equal(await page.locator(".card:visible").count(), 0);
    assert.equal(await page.locator("#random").isDisabled(), true);
    assert.equal(await page.locator("#empty").isVisible(), true);
    await page.locator("#reset").click();
    await page.locator("#minutes").selectOption("20");
    await page.locator("#budget").selectOption("0");
    await page.locator("#company").selectOption("solo");
    await page.locator("#energy").selectOption("low");
    const matching = await page.locator(".card:visible").evaluateAll(items => items.map(x => x.dataset));
    assert(matching.length > 0);
    matching.forEach(x => {
      assert(Number(x.minutes) <= 20 && Number(x.budget) === 0);
      assert(["solo", "either"].includes(x.company) && x.energy === "low");
    });
    await page.locator("#random").click();
    assert(await page.evaluate(() => document.activeElement.tagName === "SUMMARY"));
    await page.goto(url + "#j019");
    await page.waitForFunction(() => document.getElementById("j019").open);
    assert.equal(await page.locator("#j019").getAttribute("open"), "");
    await page.goto(url + "#b01");
    await page.waitForFunction(() => document.getElementById("research-content").open);
    assert.equal(await page.locator("#research-content").getAttribute("open"), "");
    await page.goto(url);
    await page.reload();
    await page.locator("#j019 > summary").focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.locator("#j019").getAttribute("open"), "");
    await page.evaluate(() => scrollTo({top: 0, behavior: "instant"}));
    await page.screenshot({path: process.env.SCREENSHOT_DESKTOP || "/tmp/enjoythemoment-desktop.png", fullPage: false});
    await page.setViewportSize({width: 390, height: 844});
    await page.goto(url);
    await page.reload();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: process.env.SCREENSHOT_MOBILE || "/tmp/enjoythemoment-mobile.png", fullPage: false});
    await page.emulateMedia({colorScheme: "dark", reducedMotion: "reduce"});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.emulateMedia({media: "print"});
    await page.evaluate(() => dispatchEvent(new Event("beforeprint")));
    assert.equal(await page.locator("details:not([open])").count(), 0);
    assert.equal(errors.length, 0, JSON.stringify(errors));
    assert.equal(requests.length, 0, JSON.stringify(requests));
    const nojs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
    const staticPage = await nojs.newPage();
    await staticPage.goto(url);
    assert.equal(await staticPage.locator(".card").count(), 60);
    assert.equal(await staticPage.locator("#filters").isVisible(), false);
    await staticPage.locator("#j001 > summary").click();
    assert.equal(await staticPage.locator("#j001 .card-body").isVisible(), true);
    await nojs.close();
    console.log("OK: offline, filters, empty state, deep links, keyboard, 390px, dark/reduced motion, print, no-JS, zero external requests");
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
