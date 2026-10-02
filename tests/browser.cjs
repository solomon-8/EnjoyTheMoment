// Optional browser QA. npm's Playwright package + a Chromium executable are required.
// They are development dependencies only; readers and builders need neither.
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

// A queued fragment scroll can move a lazy image away again after Playwright's
// initial scroll. Keep bringing it into view until it loads; do not force eager
// loading or let decode() wait forever for an offscreen image.
async function decodeImage(image) {
  await image.scrollIntoViewIfNeeded();
  await image.evaluate(async img => {
    const deadline = performance.now() + 10000;
    while (!img.complete || img.naturalWidth === 0) {
      if (performance.now() >= deadline) {
        throw new Error(`Image did not load in view: ${img.alt.slice(0, 120)}`);
      }
      img.scrollIntoView({behavior: "instant", block: "center"});
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    let timer;
    try {
      await Promise.race([
        img.decode(),
        new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error(
            `Image decode timed out: ${img.alt.slice(0, 120)}`
          )), 10000);
        })
      ]);
    } finally {
      clearTimeout(timer);
    }
  });
}

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
    await page.goto(url + "#pleasure-ground");
    await page.waitForFunction(() => document.getElementById("e01").open);
    assert.deepEqual(await page.locator("#e01 .prose h3").allTextContents(), [
      "一、先争论快乐有没有价值，而不是先算它的用途",
      "二、愿意付出什么，才是价值排序的分歧",
      "三、喜欢是理由，不是所有做法的通行证",
      "四、承认可能选错，也保留不尽兴的自由",
      "五、这套主张也必须接受自己的检验"
    ]);
    for (const anchor of ["pleasure-tradeoffs", "pleasure-conditions",
                          "pleasure-feedback", "pleasure-self-test"]) {
      await page.locator(`#e01 a[href="#${anchor}"]`).first().click();
      assert.equal(await page.evaluate(() => location.hash), "#" + anchor);
      assert(await page.locator("#e01 .prose").isVisible());
    }
    assert.match(await page.locator("#e01 .prose").textContent(), /没有证明它与“耍起”不相容/);
    assert.match(await page.locator("#e01 .prose").textContent(), /没有预测幸福感的变化/);
    assert(await page.locator("#e01 .prose h5").evaluateAll(headings =>
      headings.length === 2 && headings.every(h =>
        parseFloat(getComputedStyle(h).fontSize) >=
        parseFloat(getComputedStyle(h.closest(".prose")).fontSize))));
    await page.goto(url + "#constrained-access-authorship");
    await page.waitForFunction(() => document.getElementById("c09").open);
    assert.match(await page.locator("#c09 .prose").textContent(), /被允许参加，与有机会决定大家怎样参加/);
    assert.match(await page.locator("#c09 .prose").textContent(), /被考虑，不等于欠一份感动/);
    await page.locator("#c09 a[href='#f84']").first().click();
    await page.waitForFunction(() => document.getElementById("f84").open);
    assert.match(await page.locator("#f84 .prose").textContent(), /2026-08-04/);
    assert.match(await page.locator("#f84 .prose").textContent(), /未参加活动/);
    await page.locator("#f84 a[href='#constrained-access-scene']").first().click();
    await page.waitForFunction(() => document.getElementById("c09").open);
    await page.goto(url + "#digital-value");
    await page.waitForFunction(() => document.getElementById("e10").open);
    assert.equal(await page.locator("#e10 .prose h3").count(), 4);
    for (const anchor of ["digital-value", "digital-conditions", "digital-delegation", "digital-commercial-costs"]) {
      await page.locator(`#e10 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e10 .prose").isVisible());
    }
    assert.match(await page.locator("#e10 .prose").textContent(), /刻意假定损失存在/);
    assert.match(await page.locator("#e10 .prose").textContent(), /并不会独自解决分配问题/);
    assert(await page.locator("#e10 .prose h5").evaluateAll(headings =>
      headings.length === 3 && headings.every(h =>
        parseFloat(getComputedStyle(h).fontSize) >=
        parseFloat(getComputedStyle(h.closest(".prose")).fontSize))));
    await page.goto(url + "#digital-desire");
    await page.waitForFunction(() => document.getElementById("e10").open);
    assert.match(await page.locator("#e10 .prose").textContent(), /想要不是命令，享乐不是服从/);
    assert.match(await page.locator("#e10 .prose").textContent(), /不是三种互斥的人/);
    assert.match(await page.locator("#e10 .prose").textContent(), /旁观者不能仅凭点击宣布你不喜欢/);
    await page.locator("#e10 a[href='#n42']").first().click();
    await page.waitForFunction(() => document.getElementById("n42").open);
    assert.match(await page.locator("#n42 .prose").textContent(), /p = \.051/);
    assert.match(await page.locator("#n42 .prose").textContent(), /未取得或核读补充材料/);
    await page.locator("#n42 a[href='#digital-desire-study']").first().click();
    await page.waitForFunction(() => document.getElementById("e10").open);
    await page.goto(url);
    await page.locator("#chapter-query").fill("C13");
    await page.goto(url + "#live-participation");
    await page.waitForFunction(() => document.getElementById("c13").open);
    assert.equal(await page.locator("#c13 .prose table").count(), 3);
    assert.match(await page.locator("#c13 .prose").textContent(), /红信三票、蓝信两票/);
    for (const anchor of ["live-choice", "live-control-objection"]) {
      await page.locator(`#c13 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c13 .prose").isVisible());
    }
    await page.locator("#c13 a[href='#pleasure-promises']").first().click();
    await page.waitForFunction(() => document.getElementById("e11").open);
    assert.match(await page.locator("#e11 .prose").textContent(), /感动可以是真的/);
    await page.locator("#chapter-query").fill("不存在的共同观看XYZ");
    await page.goto(url + "#live-choice");
    await page.waitForFunction(() => document.getElementById("c13").open &&
      !document.getElementById("c13").hidden && document.getElementById("chapter-query").value === "");
    await page.locator("#c13 a[href='#celebration-same-night']").first().click();
    await page.waitForFunction(() => document.getElementById("c18").open);
    await page.locator("#c18 a[href='#connection-shared-attention']").first().click();
    await page.waitForFunction(() => document.getElementById("c05").open);
    await page.goto(url);
    await page.locator("#chapter-query").fill("热量");
    await page.locator("#c38 > summary").click();
    assert.match(await page.locator("#c38 .prose").textContent(), /不是完整单循环/);
    assert.equal(await page.locator("#c38 .prose table").count(), 2);
    const doublesImage = page.locator("#c38 .prose img");
    await doublesImage.scrollIntoViewIfNeeded();
    await page.waitForFunction(() => {
      const image = document.querySelector("#c38 .prose img");
      return image.complete && image.naturalWidth > 0;
    }, null, {timeout: 10000});
    await decodeImage(doublesImage);
    assert.deepEqual(await doublesImage.evaluate(el => [el.naturalWidth, el.naturalHeight]), [800, 1680]);
    for (const [id, anchor, phrase] of [
      ["f73", "sport-doubles", /主站目录当次访问403/],
      ["f74", "sport-court-time", /没有招募参与者/]
    ]) {
      await page.locator(`#c38 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      assert.match(await page.locator(`#${id} .prose`).textContent(), phrase);
      await page.locator("#chapter-query").fill("不存在的打球XYZ");
      await page.locator(`#${id} .prose a[href='#${anchor}']`).last().click();
      await page.waitForFunction(() => document.getElementById("c38").open &&
        !document.getElementById("c38").hidden && document.getElementById("chapter-query").value === "");
      assert.equal(new URL(page.url()).hash, "#" + anchor);
    }
    await page.goto(url);
    const entryLinks = await page.locator("#disagreements .prose h3 a").all();
    assert.equal(entryLinks.length, 5);
    assert(await page.locator("#disagreements").isVisible());
    for (const link of entryLinks) {
      const href = await link.getAttribute("href");
      await link.click();
      assert.equal(new URL(page.url()).hash, href);
      const reached = await page.locator(href).evaluate(el => {
        const container = el.closest("details");
        return container && container.open && !container.hidden;
      });
      assert.equal(reached, true, href);
    }
    await page.goto(url);
    assert.equal(await page.locator(".card").count(), 60);
    assert.equal(await page.locator("#filters").isVisible(), true);
    assert.equal(await page.locator(".argument").count(), 11);
    assert.equal(await page.locator(".playbook").count(), 10);
    assert.equal(await page.locator(".chapter-intro").count(), 38);
    await page.goto(url + "#solo-man-of-crowd");
    await page.waitForFunction(() => document.getElementById("c07").open);
    const crowdSpoiler = page.locator("#c07 .prose details");
    assert.equal(await crowdSpoiler.count(), 1);
    assert.equal(await crowdSpoiler.evaluate(el => el.open), false);
    await crowdSpoiler.locator("summary").click();
    assert.equal(await crowdSpoiler.evaluate(el => el.open), true);
    assert.match(await crowdSpoiler.textContent(), /行走路线可以被写得很详细/);
    await crowdSpoiler.locator("summary").click();
    await page.locator("#c07 a[href='#f72']").first().click();
    await page.waitForFunction(() => document.getElementById("f72").open);
    assert.match(await page.locator("#f72 .prose").textContent(), /尾随行为不是行动建议/);
    await page.locator("#chapter-query").fill("不存在的公共独处XYZ");
    await page.locator("#f72 .prose a[href='#solo-man-of-crowd']").last().click();
    await page.waitForFunction(() => document.getElementById("c07").open &&
      !document.getElementById("c07").hidden && document.getElementById("chapter-query").value === "");
    await page.goto(url + "#senses-thermal-touch");
    await page.waitForFunction(() => document.getElementById("c02").open);
    assert.match(await page.locator("#c02 .prose").textContent(), /一样的初始温度，不代表一样的接触/);
    await page.locator("#c02 a[href='#n38']").first().click();
    await page.waitForFunction(() => document.getElementById("n38").open);
    assert.match(await page.locator("#n38 .prose").textContent(), /84次是每人的试次数，不是84名参与者/);
    await page.locator("#chapter-query").fill("不存在的触感XYZ");
    await page.locator("#n38 .prose a[href='#senses-thermal-touch']").click();
    await page.waitForFunction(() => document.getElementById("c02").open &&
      !document.getElementById("c02").hidden && document.getElementById("chapter-query").value === "");
    await page.goto(url + "#celebration-west-lake");
    await page.waitForFunction(() => document.getElementById("c18").open);
    assert.match(await page.locator("#c18 .prose").textContent(),
      /不是永远没有人的西湖/);
    assert.equal(await page.locator("#c18 .prose details").count(), 1);
    assert.equal(await page.locator("#c18 .prose details").evaluate(e => e.open), false);
    await page.locator("#c18 a[href='#f81']").click();
    await page.waitForFunction(() => document.getElementById("f81").open);
    assert.match(await page.locator("#f81 .prose").textContent(),
      /未提供版本信息的页面/);
    assert.match(await page.locator("#f81 .prose").textContent(),
      /不是今天的饮酒、夜航或人群安全建议/);
    await page.locator("#chapter-query").fill("不存在的共同节日XYZ");
    await page.locator("#f81 a[href='#celebration-west-lake']").click();
    await page.waitForFunction(() => document.getElementById("c18").open &&
      !document.getElementById("c18").hidden &&
      document.getElementById("chapter-query").value === "");
    await page.goto(url + "#nightlife-syncopation");
    await page.waitForFunction(() => document.getElementById("c37").open);
    assert.equal(await page.locator("#c37 table").count(), 3);
    assert.match(await page.locator("#c37 .prose").textContent(),
      /知道下一拍在哪里，不等于已经经历过下一拍/);
    await page.locator("#c37 a[href='#n41']").first().click();
    await page.waitForFunction(() => document.getElementById("n41").open);
    assert.match(await page.locator("#n41 .prose").textContent(), /p = \.178/);
    assert.match(await page.locator("#n41 .prose").textContent(), /作者声明，不是本书复现结论/);
    await page.locator("#chapter-query").fill("不存在的切分XYZ");
    await page.locator("#n41 a[href='#nightlife-repeat-participation']").click();
    await page.waitForFunction(() => document.getElementById("c37").open &&
      !document.getElementById("c37").hidden &&
      document.getElementById("chapter-query").value === "");
    await page.goto(url + "#nightlife-sequence");
    await page.waitForFunction(() => document.getElementById("c37").open);
    assert.match(await page.locator("#c37 .prose").textContent(), /甲合计八格，乙合计六格/);
    const nightlifeImage = page.locator("#c37 .prose img");
    await nightlifeImage.scrollIntoViewIfNeeded();
    await decodeImage(nightlifeImage);
    assert.equal(await nightlifeImage.evaluate(image => image.naturalWidth), 800);
    await page.locator("#c37 a[href='#f71']").first().click();
    await page.waitForFunction(() => document.getElementById("f71").open);
    assert.match(await page.locator("#f71 .prose").textContent(), /两种说法不一致/);
    await page.locator("#chapter-query").fill("不存在的夜生活XYZ");
    await page.locator("#f71 .prose a[href='#c37']").click();
    await page.waitForFunction(() => document.getElementById("c37").open &&
      !document.getElementById("c37").hidden && document.getElementById("chapter-query").value === "");
    await page.goto(url + "#novelty-repeat");
    await page.waitForFunction(() => document.getElementById("c03").open);
    assert.match(await page.locator("#c03 .prose").textContent(), /同样的快乐，为什么一到第二次就像贬值了/);
    assert.match(await page.locator("#c03 .prose").textContent(), /最强的反对意见/);
    await page.locator("#c03 a[href='#n37']").first().click();
    await page.waitForFunction(() => document.getElementById("n37").open);
    assert.match(await page.locator("#n37 .prose").textContent(), /没有实际扣款，也没有第二轮观看结果/);
    assert.equal(await page.locator("#n37 .prose table").count(), 2);
    await page.locator("#chapter-query").fill("不存在的重复研究XYZ");
    await page.locator("#n37 .prose a[href='#novelty-repeat']").click();
    await page.waitForFunction(() => document.getElementById("c03").open &&
      !document.getElementById("c03").hidden && document.getElementById("chapter-query").value === "");
    await page.goto(url + "#home-modes");
    await page.waitForFunction(() => document.getElementById("c36").open);
    assert.equal(await page.locator("#c36 .prose table").count(), 1);
    const homeImage = page.locator("#c36 .prose img");
    await decodeImage(homeImage);
    assert.deepEqual(await homeImage.evaluate(el => [el.naturalWidth, el.naturalHeight]), [800, 2080]);
    assert.match(await homeImage.getAttribute("alt"), /遮挡没有封闭成房间/);
    await page.locator("#c36 a[href='#f70']").first().click();
    await page.waitForFunction(() => document.getElementById("f70").open);
    assert.match(await page.locator("#f70 .prose").textContent(), /没有取得并通读该书/);
    await page.locator("#chapter-query").fill("不存在的居住XYZ");
    await page.locator("#f70 a[href='#home-view']").last().click();
    await page.waitForFunction(() => document.getElementById("c36").open &&
      !document.getElementById("c36").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#home-view");
    await page.goto(url + "#intimacy-value");
    await page.waitForFunction(() => document.getElementById("c35").open);
    assert.equal(await page.locator("#c35 .prose table").count(), 2);
    assert.match(await page.locator("#c35 .prose").textContent(), /亲密不必拿次数证明/);
    for (const [id, anchor, phrase] of [
      ["n36", "intimacy-frequency", /没有回答自发发生/],
      ["f69", "intimacy-spectrum", /不代表WHO正式立场/]
    ]) {
      await page.locator(`#c35 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      assert.match(await page.locator(`#${id} .prose`).textContent(), phrase);
      await page.locator("#chapter-query").fill("不存在的亲密XYZ");
      await page.locator(`#${id} a[href='#${anchor}']`).last().click();
      await page.waitForFunction(() => document.getElementById("c35").open &&
        !document.getElementById("c35").hidden && document.getElementById("chapter-query").value === "");
      assert.equal(new URL(page.url()).hash, "#" + anchor);
    }
    await page.goto(url);
    await page.locator(".primary").click();
    await page.waitForFunction(() => document.getElementById("shuaqi-content").open);
    assert.equal(new URL(page.url()).hash, "#shuaqi-content");
    for (const anchor of ["shuaqi-position", "shuaqi-costs", "shuaqi-objections", "shuaqi-reading"]) {
      await page.locator(`#shuaqi-content a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#shuaqi-content .prose").isVisible());
    }
    await page.locator("#essay-query").fill("不存在的论证XYZ");
    assert.equal(await page.locator("#e01").isVisible(), false);
    await page.locator("#shuaqi-content a[href='#pleasure-options']").first().click();
    await page.waitForFunction(() => document.getElementById("e01").open &&
      !document.getElementById("e01").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#pleasure-options");
    assert(await page.locator("#e01").isVisible());
    await page.locator("#e01 a[href='#pleasure-enough']").first().click();
    assert.equal(new URL(page.url()).hash, "#pleasure-enough");
    assert.match(await page.locator("#e01 .prose").textContent(), /不存在的晚上/);
    await page.locator("#e01 a[href='#shuaqi-position']").first().click();
    assert.equal(new URL(page.url()).hash, "#shuaqi-position");
    await page.locator("#shuaqi-content > summary").click();
    await page.goto(url + "#connection-shared-attention");
    await page.waitForFunction(() => document.getElementById("c05").open);
    assert.equal(await page.locator("#c05 .prose table").count(), 1);
    for (const anchor of ["connection-shared-attention", "connection-amplification", "connection-not-a-tool"]) {
      await page.locator(`#c05 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c05 .prose").isVisible());
    }
    for (const [note, target] of [["n21", "connection-amplification"], ["n22", "connection-distance"]]) {
      await page.locator(`#c05 a[href='#${note}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open && !document.getElementById(id).hidden, note);
      assert.equal(new URL(page.url()).hash, "#" + note);
      assert(await page.locator(`#${note} .prose`).isVisible());
      await page.locator("#chapter-query").fill("不存在的章节XYZ");
      await page.locator(`#${note} a[href='#${target}']`).first().click();
      await page.waitForFunction(() => document.getElementById("c05").open && !document.getElementById("c05").hidden);
      assert.equal(new URL(page.url()).hash, "#" + target);
    }
    await page.goto(url + "#time-overlap");
    await page.waitForFunction(() => document.getElementById("c21").open);
    assert.equal(await page.locator("#c21 .prose table").count(), 2);
    for (const anchor of ["time-overlap", "time-empty", "time-study"]) {
      await page.locator(`#c21 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c21 .prose").isVisible());
    }
    await page.locator("#c21 a[href='#n27']").first().click();
    await page.waitForFunction(() => document.getElementById("n27").open);
    assert.match(await page.locator("#n27 .prose").textContent(), /p = .066/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#n27 a[href='#time-study']").first().click();
    await page.waitForFunction(() => document.getElementById("c21").open &&
      !document.getElementById("c21").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#time-study");
    // An edited section keeps its old fragment and routes to the same chapter.
    await page.goto(url + "#" + encodeURIComponent("不给空白写用途是否就是浪费"));
    await page.waitForFunction(() => document.getElementById("c21").open);
    await page.locator("#c21 a[href='#time-reservation']").first().click();
    assert.equal(new URL(page.url()).hash, "#time-reservation");
    assert.match(await page.locator("#c21 .prose").textContent(), /原创假想/);
    await page.locator("#essay-query").fill("不存在的休息XYZ");
    await page.locator("#c21 a[href='#rest-no-verdict']").first().click();
    await page.waitForFunction(() => document.getElementById("e07").open &&
      !document.getElementById("e07").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#rest-no-verdict");
    await page.goto(url + "#friends-not-a-service");
    await page.waitForFunction(() => document.getElementById("e09").open);
    await page.locator("#e09 a[href='#friends-reciprocity']").first().click();
    assert.equal(new URL(page.url()).hash, "#friends-reciprocity");
    await page.goto(url + "#friends-exchange-study");
    await page.waitForFunction(() => document.getElementById("e09").open);
    assert.equal(await page.locator("#e09 .prose table tbody tr").count(), 2);
    assert.match(await page.locator("#e09 .prose").textContent(), /不是两项实验实际检验的结果/);
    await page.locator("#e09 a[href='#n39']").first().click();
    await page.waitForFunction(() => document.getElementById("n39").open);
    assert.equal(await page.locator("#n39 .prose table").count(), 3);
    assert.match(await page.locator("#n39 .prose").textContent(), /这项预测没有得到支持/);
    await page.locator("#n39 a[href='#e09']").first().click();
    await page.waitForFunction(() => document.getElementById("e09").open);
    await page.locator("#e09 a[href='#f57']").first().click();
    await page.waitForFunction(() => document.getElementById("f57").open);
    assert.match(await page.locator("#f57 .prose").textContent(), /没有通读全书/);
    await page.locator("#essay-query").fill("不存在的关系XYZ");
    await page.locator("#f57 a[href='#friends-ending']").first().click();
    await page.waitForFunction(() => document.getElementById("e09").open &&
      !document.getElementById("e09").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#friends-ending");
    await page.goto(url + "#audience-not-a-purity-test");
    await page.waitForFunction(() => document.getElementById("e08").open);
    for (const anchor of ["audience-three-requests", "audience-admiration",
                         "audience-sharing-intention", "audience-chosen-tradeoff",
                         "audience-staging", "audience-verdict"]) {
      await page.locator(`#e08 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e08 .prose").isVisible());
    }
    await page.locator("#e08 a[href='#n10']").first().click();
    await page.waitForFunction(() => document.getElementById("n10").open);
    assert.match(await page.locator("#n10 .prose").textContent(), /不是本研究的实测结果/);
    await page.locator("#essay-query").fill("未匹配的观众XYZ");
    await page.locator("#n10 a[href='#audience-photo-study']").first().click();
    await page.waitForFunction(() => document.getElementById("e08").open &&
      !document.getElementById("e08").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#audience-photo-study");
    await page.locator("#e08 a[href='#n44']").first().click();
    await page.waitForFunction(() => document.getElementById("n44").open);
    assert.match(await page.locator("#n44 .prose").textContent(), /abstract_only/);
    assert.match(await page.locator("#n44 .prose").textContent(), /未取得主文/);
    await page.locator("#n44 a[href='#audience-chosen-tradeoff']").first().click();
    await page.waitForFunction(() => document.getElementById("e08").open);
    assert.equal(new URL(page.url()).hash, "#audience-chosen-tradeoff");
    await page.goto(url + "#amateur-purpose");
    await page.waitForFunction(() => document.getElementById("e05").open);
    assert.equal(await page.locator("#e05 .prose h3").count(), 4);
    for (const anchor of ["amateur-purpose", "amateur-methods", "amateur-together", "amateur-companions"]) {
      await page.locator(`#e05 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e05 .prose").isVisible());
    }
    assert.match(await page.locator("#e05 .prose").textContent(), /不是原来快乐的无损替代/);
    assert.match(await page.locator("#e05 .prose").textContent(), /不能用改组取消已有责任/);
    assert(await page.locator("#e05 .prose h5").evaluateAll(headings =>
      headings.length === 3 && headings.every(h =>
        parseFloat(getComputedStyle(h).fontSize) >=
        parseFloat(getComputedStyle(h.closest(".prose")).fontSize))));
    await page.goto(url + "#amateur-want-better");
    await page.waitForFunction(() => document.getElementById("e05").open);
    for (const anchor of ["amateur-practice-study", "amateur-shared-standards", "amateur-criticism"]) {
      await page.locator(`#e05 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e05 .prose").isVisible());
    }
    await page.locator("#e05 a[href='#n25']").first().click();
    await page.waitForFunction(() => document.getElementById("n25").open);
    assert.match(await page.locator("#n25 .prose").textContent(), /摘要和图3仍显示原报告/);
    await page.locator("#essay-query").fill("未匹配的爱好XYZ");
    await page.locator("#n25 a[href='#amateur-practice-study']").first().click();
    await page.waitForFunction(() => document.getElementById("e05").open &&
      !document.getElementById("e05").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#amateur-practice-study");
    await page.locator("#e05 a[href='#amateur-effective-for-what']").first().click();
    assert.equal(new URL(page.url()).hash, "#amateur-effective-for-what");
    await page.locator("#e05 a[href='#n43']").first().click();
    await page.waitForFunction(() => document.getElementById("n43").open);
    assert.match(await page.locator("#n43 .prose").textContent(), /实验2不是等总时长比较/);
    assert.match(await page.locator("#n43 .prose").textContent(), /t\(58\) = 1.21/);
    await page.locator("#n43 a[href='#amateur-effective-for-what']").first().click();
    await page.waitForFunction(() => document.getElementById("e05").open);
    assert.equal(new URL(page.url()).hash, "#amateur-effective-for-what");
    await page.goto(url + "#constraints-necessity");
    await page.waitForFunction(() => document.getElementById("e06").open);
    for (const anchor of ["constraints-wishes", "constraints-shared-evening",
                         "constraints-conflicting-evenings", "constraints-conditions",
                         "constraints-options", "constraints-standing",
                         "constraints-help", "constraints-permission-study"]) {
      await page.locator(`#e06 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e06 .prose").isVisible());
    }
    await page.locator("#e06 a[href='#n26']").first().click();
    await page.waitForFunction(() => document.getElementById("n26").open);
    assert.match(await page.locator("#n26 .prose").textContent(), /4,189/);
    await page.locator("#essay-query").fill("没有匹配的必要性XYZ");
    await page.locator("#n26 a[href='#constraints-permission-study']").first().click();
    await page.waitForFunction(() => document.getElementById("e06").open &&
      !document.getElementById("e06").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#constraints-permission-study");
    await page.goto(url + "#rest-returns");
    await page.waitForFunction(() => document.getElementById("e07").open);
    for (const anchor of ["rest-lafargue", "rest-productivity-defense",
                         "rest-leisure-command", "rest-real-income", "rest-paid-evening",
                         "rest-service-work", "rest-service-ending",
                         "rest-paid-service", "rest-less-convenience"]) {
      await page.locator(`#e07 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e07 .prose").isVisible());
    }
    assert.match(await page.locator("#e07 .prose").textContent(), /耍起，不该只对买单的人说/);
    assert.match(await page.locator("#e07 .prose").textContent(), /经济需要让一切同意作废/);
    await page.locator("#e07 a[href='#f82']").first().click();
    await page.waitForFunction(() => document.getElementById("f82").open);
    assert.match(await page.locator("#f82 .prose").textContent(), /英译第四节开头/);
    assert.match(await page.locator("#f82 .prose").textContent(), /十人、八小时与六小时/);
    await page.locator("#essay-query").fill("不存在的劳动崇拜XYZ");
    await page.locator("#f82 a[href='#rest-productivity-defense']").click();
    await page.waitForFunction(() => document.getElementById("e07").open &&
      !document.getElementById("e07").hidden && document.getElementById("essay-query").value === "");
    assert.match(await page.locator("#e07 .prose").textContent(), /质量、收入、需求和人员都不变/);
    await page.locator("#essay-query").fill("未匹配论证XYZ");
    await page.evaluate(() => { window.location.hash = "#rest-no-verdict"; });
    await page.waitForFunction(() => document.getElementById("e07").open &&
      !document.getElementById("e07").hidden && document.getElementById("essay-query").value === "");
    assert.match(await page.locator("#e07 .prose").textContent(), /不喜欢这次安排，不等于没有资格拥有这段时间/);
    await page.goto(url + "#excitement-information");
    await page.waitForFunction(() => document.getElementById("e02").open);
    await page.locator("#e02 a[href='#excitement-costs']").first().click();
    assert.equal(new URL(page.url()).hash, "#excitement-costs");
    await page.locator("#e02 a[href='#n24']").first().click();
    await page.waitForFunction(() => document.getElementById("n24").open);
    assert.match(await page.locator("#n24 .prose").textContent(), /不熟悉的回答按0处理/);
    await page.locator("#essay-query").fill("未匹配论证XYZ");
    await page.locator("#n24 a[href='#excitement-study']").first().click();
    await page.waitForFunction(() => document.getElementById("e02").open &&
      !document.getElementById("e02").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#excitement-study");
    await page.goto(url + "#waiting-credible-promise");
    await page.waitForFunction(() => document.getElementById("e03").open);
    assert(await page.locator("#e03 .prose").isVisible());
    assert.equal(await page.locator("#e03 .prose h3").count(), 5);
    assert.match(await page.locator("#e03 .prose").textContent(), /不是三类人，也不是互斥选项/);
    for (const anchor of ["waiting-credible-promise", "waiting-long-term-defense",
                         "waiting-not-a-patience-score", "waiting-real-window",
                         "waiting-future-self", "waiting-anticipation"]) {
      await page.locator(`#e03 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e03 .prose").isVisible());
    }
    await page.locator("#e03 a[href='#waiting-long-term-defense']").first().click();
    assert.equal(new URL(page.url()).hash, "#waiting-long-term-defense");
    await page.locator("#e03 a[href='#n23']").first().click();
    await page.waitForFunction(() => document.getElementById("n23").open);
    assert.match(await page.locator("#n23 .prose").textContent(), /右截尾/);
    await page.locator("#essay-query").fill("未匹配论证XYZ");
    await page.locator("#n23 a[href='#waiting-marshmallow']").first().click();
    await page.waitForFunction(() => document.getElementById("e03").open &&
      !document.getElementById("e03").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#waiting-marshmallow");
    await page.goto(url + "#waiting-not-a-patience-score");
    await page.waitForFunction(() => document.getElementById("e03").open);
    assert.match(await page.locator("#e03 .prose").textContent(), /及时享乐不等于及时省事/);
    assert.equal(await page.locator("#e03 .prose table").count(), 2);
    await page.locator("#e03 a[href='#f75']").first().click();
    await page.waitForFunction(() => document.getElementById("f75").open);
    assert.match(await page.locator("#f75 .prose").textContent(), /同时作答与实际重测/);
    assert.equal(await page.locator("#f75 .prose table").count(), 1);
    await page.locator("#essay-query").fill("未匹配时间选择XYZ");
    await page.locator("#f75 .prose a[href='#waiting-reversal']").last().click();
    await page.waitForFunction(() => document.getElementById("e03").open &&
      !document.getElementById("e03").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#waiting-reversal");
    await page.goto(url + "#c24");
    await page.waitForFunction(() => document.getElementById("c24").open);
    assert.equal(await page.locator("#c24 .prose table").count(), 2);
    for (const anchor of ["humor-sandwich", "humor-language", "humor-time",
                          "humor-return", "humor-attention"]) {
      await page.locator(`#c24 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c24 .prose").isVisible());
    }
    const comicFold = page.locator("#c24 .prose details");
    assert.equal(await comicFold.count(), 1);
    assert.equal(await comicFold.locator("p").first().isVisible(), false);
    await comicFold.locator("summary").click();
    assert(await comicFold.locator("p").first().isVisible());
    await page.locator("#c24 a[href='#f37']").first().click();
    await page.waitForFunction(() => document.getElementById("f37").open);
    await page.locator("#f37 a[href='#c24']").click();
    await page.waitForFunction(() => document.getElementById("c24").open);
    await page.goto(url + "#c22");
    await page.waitForFunction(() => document.getElementById("c22").open);
    const readingSpoiler = page.locator("#c22 .prose details").first();
    assert.equal(await readingSpoiler.getAttribute("open"), null);
    await readingSpoiler.locator("summary").click();
    assert.match(await readingSpoiler.textContent(), /恒河/);
    await readingSpoiler.locator("summary").click();
    await page.locator("#c22 a[href='#f53']").first().click();
    await page.waitForFunction(() => document.getElementById("f53").open);
    assert.equal(await page.locator("#f53 .prose details").getAttribute("open"), null);
    await page.locator("#f53 a[href='#reading-open-window']").last().click();
    assert.equal(new URL(page.url()).hash, "#reading-open-window");
    assert(await page.locator("#c22 .prose").isVisible());
    assert.equal(await readingSpoiler.getAttribute("open"), null);
    await page.goto(url + "#c34");
    await page.waitForFunction(() => document.getElementById("c34").open);
    assert.equal(await page.locator("#c34 .prose table").count(), 5);
    for (const anchor of ["story-choice", "story-dice", "story-aspects", "story-table",
                         "story-clocks", "story-flashbacks", "story-uncertainty"]) {
      await page.locator(`#c34 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c34 .prose").isVisible());
    }
    for (const [id, target] of [["f32", "c34"], ["f33", "c34"], ["f65", "story-flashbacks"]]) {
      await page.locator(`#c34 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#${target}']`).click();
      await page.waitForFunction(() => document.getElementById("c34").open);
      assert.equal(new URL(page.url()).hash, "#" + target);
    }
    await page.goto(url + "#c33");
    await page.waitForFunction(() => document.getElementById("c33").open);
    assert.equal(await page.locator("#c33 .prose table").count(), 4);
    for (const anchor of ["singing-transpose", "singing-timbre", "singing-together", "singing-microphone"]) {
      await page.locator(`#c33 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c33 .prose").isVisible());
    }
    for (const id of ["f30", "f31"]) {
      await page.locator(`#c33 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c33']`).click();
      await page.waitForFunction(() => document.getElementById("c33").open);
    }
    await page.locator("#c33 a[href='#singing-paghjella']").click();
    assert.equal(new URL(page.url()).hash, "#singing-paghjella");
    await page.locator("#c33 a[href='#f62']").first().click();
    await page.waitForFunction(() => document.getElementById("f62").open);
    assert.match(await page.locator("#f62 .prose").textContent(), /完整核读决定正文/);
    assert.match(await page.locator("#f62 .prose").textContent(), /HTTP 200 不能当作成功读到正文/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f62 a[href='#singing-role-choice']").click();
    await page.waitForFunction(() => document.getElementById("c33").open &&
      !document.getElementById("c33").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#singing-role-choice");
    await page.goto(url + "#play-wanting-to-win");
    await page.waitForFunction(() => document.getElementById("c04").open);
    assert.equal(await page.locator("#c04 .prose table").count(), 1);
    assert.equal(await page.locator("#c04 .prose table tbody tr").count(), 2);
    assert.match(await page.locator("#c04 .prose").textContent(), /总和正好为 9/);
    await page.locator("#c04 a[href='#play-changing-goals']").click();
    assert.equal(new URL(page.url()).hash, "#play-changing-goals");
    await page.locator("#c04 a[href='#f63']").first().click();
    await page.waitForFunction(() => document.getElementById("f63").open);
    assert.match(await page.locator("#f63 .prose").textContent(), /没有独立核读 Suits 原书/);
    assert.match(await page.locator("#f63 .prose").textContent(), /没有将抽取等同整篇核读/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f63 a[href='#play-score-boundary']").click();
    await page.waitForFunction(() => document.getElementById("c04").open &&
      !document.getElementById("c04").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#play-score-boundary");
    await page.goto(url + "#e11");
    await page.waitForFunction(() => document.getElementById("e11").open);
    assert.equal(await page.locator("#e11 .prose table").count(), 2);
    assert.equal(await page.locator("#e11 .prose table").first().locator("tbody tr").count(), 4);
    assert.equal(await page.locator("#e11 .prose table").nth(1).locator("tbody tr").count(), 3);
    await page.locator("#e11 a[href='#pleasure-virtual']").click();
    assert.equal(new URL(page.url()).hash, "#pleasure-virtual");
    assert(await page.locator("#e11 .prose").isVisible());
    await page.locator("#e11 a[href='#f27']").first().click();
    await page.waitForFunction(() => document.getElementById("f27").open);
    assert.match(await page.locator("#f27 .prose").textContent(), /没有直接核读/);
    await page.locator("#f27 a[href='#e11']").click();
    await page.waitForFunction(() => document.getElementById("e11").open);
    await page.locator("#e11 a[href='#pleasure-digital-life']").click();
    assert.equal(new URL(page.url()).hash, "#pleasure-digital-life");
    await page.locator("#e11 a[href='#f59']").first().click();
    await page.waitForFunction(() => document.getElementById("f59").open);
    assert.match(await page.locator("#f59 .prose").textContent(), /没有完整核读/);
    assert.match(await page.locator("#f59 .prose").textContent(), /不是现有头显/);
    await page.locator("#essay-query").fill("不存在的长文XYZ");
    await page.locator("#f59 a[href='#pleasure-promises']").click();
    await page.waitForFunction(() => document.getElementById("e11").open &&
      !document.getElementById("e11").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#pleasure-promises");
    for (const anchor of ["pleasure-taste-claims", "pleasure-taste-key",
                          "pleasure-taste-choice", "pleasure-taste-criticism"]) {
      await page.locator(`#e11 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#e11 .prose").isVisible());
    }
    await page.locator("#e11 a[href='#f83']").first().click();
    await page.waitForFunction(() => document.getElementById("f83").open);
    assert.match(await page.locator("#f83 .prose").textContent(), /没有独立核读塞万提斯原作/);
    assert.match(await page.locator("#f83 .prose").textContent(), /没有把 ST 29 的年龄例子当作现代年龄规律/);
    await page.locator("#essay-query").fill("不存在的趣味论XYZ");
    await page.locator("#f83 a[href='#pleasure-taste-choice']").click();
    await page.waitForFunction(() => document.getElementById("e11").open &&
      !document.getElementById("e11").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#pleasure-taste-choice");
    await page.goto(url + "#e01");
    await page.waitForFunction(() => document.getElementById("e01").open);
    await page.locator("#e01 a[href='#e11']").click();
    assert.equal(new URL(page.url()).hash, "#e11");
    await page.locator("#chapter-query").fill("C02");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.locator("#chapter-query").fill("套餐 风味");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.locator("#chapter-query").fill("不存在的章节87765");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 0);
    await page.goto(url + "#c03");
    await page.waitForFunction(() => document.getElementById("c03").open);
    assert.equal(await page.locator("#chapter-query").inputValue(), "");
    assert.match(await page.locator("#c03 .prose").textContent(), /新鲜感，不是生活不及格后的补考/);
    await page.goto(url + "#c06");
    await page.waitForFunction(() => document.getElementById("c06").open);
    assert.equal(await page.locator("#c06 .prose table").count(), 4);
    await page.locator("#c06 a[href='#spending-matching-life']").first().click();
    assert.equal(new URL(page.url()).hash, "#spending-matching-life");
    assert.match(await page.locator("#c06 .prose").textContent(), /不必让生活通过物品的验收/);
    await page.locator("#c06 a[href='#f76']").first().click();
    await page.waitForFunction(() => document.getElementById("f76").open);
    assert.match(await page.locator("#f76 .prose").textContent(), /未完成全篇逐字图文对校/);
    await page.locator("#f76 a[href='#spending-matching-life']").first().click();
    await page.waitForFunction(() => document.getElementById("c06").open);
    await page.goto(url + "#c08");
    await page.waitForFunction(() => document.getElementById("c08").open);
    assert.equal(await page.locator("#c08 .prose table").count(), 2);
    await page.locator("#c08 a[href='#permission-status']").click();
    assert.equal(new URL(page.url()).hash, "#permission-status");
    await page.locator("#c08 a[href='#f60']").first().click();
    await page.waitForFunction(() => document.getElementById("f60").open);
    assert.match(await page.locator("#f60 .prose").textContent(), /完整核读第三章，不是完整核读全书/);
    assert.match(await page.locator("#f60 .prose").textContent(), /不是当代人群调查/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f60 a[href='#permission-vicarious']").click();
    await page.waitForFunction(() => document.getElementById("c08").open &&
      !document.getElementById("c08").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#permission-vicarious");
    await page.locator("#c08 a[href='#n05']").click();
    await page.waitForFunction(() => document.getElementById("n05").open);
    assert.match(await page.locator("#n05 .prose").textContent(), /p = \.053/);
    assert.match(await page.locator("#n05 .prose").textContent(), /p = \.84/);
    await page.goto(url + "#c07");
    await page.waitForFunction(() => document.getElementById("c07").open);
    await page.locator("#c07 a[href='#n06']").click();
    await page.waitForFunction(() => document.getElementById("n06").open);
    assert.match(await page.locator("#n06 .prose").textContent(), /p = \.032/);
    await page.goto(url + "#c09");
    await page.waitForFunction(() => document.getElementById("c09").open);
    await page.locator("#c09 a[href='#f01']").click();
    await page.waitForFunction(() => document.getElementById("f01").open);
    assert.match(await page.locator("#f01 .prose").textContent(), /不是每个人连续记了七天/);
    await page.goto(url + "#c10");
    await page.waitForFunction(() => document.getElementById("c10").open);
    assert.match(await page.locator("#c10 .prose").textContent(), /“那一刻很好”与“整个安排不值得”/);
    await page.locator("#chapter-query").fill("C12");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c12");
    await page.waitForFunction(() => document.getElementById("c12").open);
    assert.match(await page.locator("#c12 .prose").textContent(), /长镜头说的是镜头持续/);
    assert.equal(await page.locator("#c12 .prose table").count(), 4);
    assert.equal(await page.locator("#c12 .artwork img").count(), 3);
    assert.equal(await page.locator("#c12 .prose details").getAttribute("open"), null);
    assert.equal(await page.locator("#c12 .prose details img").isVisible(), false);
    await page.locator("#c12 .prose details > summary").click();
    for (const image of await page.locator("#c12 .artwork img").all()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.ok(await image.evaluate(img => img.naturalWidth > 0 && img.alt.length > 30));
    }
    await page.locator("#c12 .prose details > summary").click();
    await page.locator("#c12 a[href='#f16']").first().click();
    await page.waitForFunction(() => document.getElementById("f16").open);
    assert.match(await page.locator("#f16 .prose").textContent(), /不是连续完整播放/);
    await page.goto(url + "#c12");
    await page.locator("#c12 a[href='#f03']").click();
    await page.waitForFunction(() => document.getElementById("f03").open);
    assert.match(await page.locator("#f03 .prose").textContent(), /实际依据是条目的文字解释/);
    await page.goto(url + "#film-designed-emotion");
    await page.waitForFunction(() => document.getElementById("c12").open);
    assert.match(await page.locator("#c12 .prose").textContent(), /我已经哭了，我仍可以觉得它拍得不好/);
    for (const [source, anchor, marker] of [
      ["n32", "film-context-study", /同一序列内的重复/],
      ["n33", "film-context-boundary", /p = \.293/],
    ]) {
      await page.locator(`#c12 a[href='#${source}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, source);
      assert.match(await page.locator(`#${source} .prose`).textContent(), marker);
      await page.locator("#chapter-query").fill("不存在的电影XYZ");
      await page.locator(`#${source} a[href='#${anchor}']`).first().click();
      await page.waitForFunction(() => document.getElementById("c12").open &&
        !document.getElementById("c12").hidden && document.getElementById("chapter-query").value === "");
      assert.equal(new URL(page.url()).hash, "#" + anchor);
    }
    await page.goto(url + "#c11");
    await page.waitForFunction(() => document.getElementById("c11").open);
    assert.equal(await page.locator("#c11 .prose table").count(), 4);
    await page.locator("#c11 a[href='#music-natural']").click();
    assert.equal(new URL(page.url()).hash, "#music-natural");
    await page.locator("#c11 a[href='#n31']").first().click();
    await page.waitForFunction(() => document.getElementById("n31").open);
    assert.match(await page.locator("#n31 .prose").textContent(), /p = .31/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#n31 a[href='#music-natural']").click();
    await page.waitForFunction(() => document.getElementById("c11").open &&
      !document.getElementById("c11").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#music-natural");
    assert.equal(await page.locator("#c11 .artwork img").count(), 2);
    for (const image of await page.locator("#c11 .artwork img").all()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.ok(await image.evaluate(img => img.naturalWidth > 0 && img.alt.length > 30));
    }
    await page.screenshot({path: "/tmp/enjoythemoment-music-desktop.png", fullPage: false});
    await page.locator("#c11 a[href='#f15']").first().click();
    await page.waitForFunction(() => document.getElementById("f15").open);
    assert.match(await page.locator("#f15 .prose").textContent(), /没有实际试听/);
    await page.goto(url + "#c13");
    await page.waitForFunction(() => document.getElementById("c13").open);
    await page.locator("#c13 a[href='#f04']").click();
    await page.waitForFunction(() => document.getElementById("f04").open);
    assert.match(await page.locator("#f04 .prose").textContent(), /技术标准 PDF 本次未能成功获取/);
    await page.goto(url + "#c14");
    await page.waitForFunction(() => document.getElementById("c14").open);
    await page.locator("#c14 a[href='#f05']").first().click();
    await page.waitForFunction(() => document.getElementById("f05").open);
    assert.match(await page.locator("#f05 .prose").textContent(), /没有进行盲品/);
    await page.locator("#chapter-query").fill("C15");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c15");
    await page.waitForFunction(() => document.getElementById("c15").open);
    assert.equal(await page.locator("#c15 .prose table").count(), 3);
    for (const anchor of ["street-counts", "street-midtown", "street-seats", "street-unscheduled", "street-conflicts"]) {
      await page.locator(`#c15 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c15 .prose").isVisible());
    }
    for (const id of ["f35", "f36"]) {
      await page.locator(`#c15 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c15']`).click();
      await page.waitForFunction(() => document.getElementById("c15").open);
    }
    await page.locator("#c15 a[href='#f06']").click();
    await page.waitForFunction(() => document.getElementById("f06").open);
    assert.match(await page.locator("#f06 .prose").textContent(), /没有实地评估任何街区/);
    await page.goto(url + "#e02");
    await page.waitForFunction(() => document.getElementById("e02").open);
    await page.locator("#e02 a[href='#n03']").click();
    await page.waitForFunction(() => document.getElementById("n03").open);
    assert.match(await page.locator("#n03 .prose").textContent(), /德国为 49.7%/);
    await page.goto(url + "#c01");
    await page.waitForFunction(() => document.getElementById("c01").open);
    assert.match(await page.locator("#c01 .prose").textContent(), /想要一个晚上，别总被劝成五分钟/);
    await page.locator("#chapter-query").fill("C16");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c16");
    await page.waitForFunction(() => document.getElementById("c16").open);
    assert.match(await page.locator("#c16 .prose").textContent(), /镜子里的合适，与身体里的合适/);
    for (const [chapter, anchor, evidence] of [
      ["c14", "flavor-ice-cream", "f25"],
      ["c16", "dress-form-examples", "f26"],
    ]) {
      await page.goto(url + "#" + chapter);
      await page.locator("#" + chapter + " a[href='#" + anchor + "']").click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#" + chapter + " .prose").isVisible());
      const images = page.locator("#" + chapter + " .artwork img");
      assert.equal(await images.count(), chapter === "c16" ? 2 : 1);
      const image = images.first();
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), 880);
      await page.screenshot({path: "/tmp/enjoythemoment-" + chapter + "-detail-desktop.png", fullPage: false});
      await page.locator("#" + chapter + " a[href='#" + evidence + "']").first().click();
      await page.waitForFunction(id => document.getElementById(id).open, evidence);
    }
    assert.match(await page.locator("#f26 .prose").textContent(), /未独立核对销售账册/);
    await page.goto(url + "#c16");
    for (const anchor of ["dress-pocket-object", "dress-private-beauty"]) {
      await page.locator(`#c16 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
    }
    const pocketImage = page.locator("#c16 .artwork img").nth(1);
    await pocketImage.scrollIntoViewIfNeeded();
    await decodeImage(pocketImage);
    assert.deepEqual(await pocketImage.evaluate(img => [img.naturalWidth, img.naturalHeight]), [880, 833]);
    assert.match(await pocketImage.getAttribute("alt"), /中央竖向开口/);
    await page.locator("#c16 a[href='#f66']").first().click();
    await page.waitForFunction(() => document.getElementById("f66").open);
    assert.match(await page.locator("#f66 .prose").textContent(), /不是仅凭数据集许可/);
    await page.locator("#chapter-query").fill("不存在的衣服XYZ");
    await page.locator("#f66 a[href='#dress-carrying-tradeoffs']").click();
    await page.waitForFunction(() => document.getElementById("c16").open &&
      !document.getElementById("c16").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#dress-carrying-tradeoffs");
    await page.locator("#c16 a[href='#f08']").click();
    await page.waitForFunction(() => document.getElementById("f08").open);
    assert.match(await page.locator("#f08 .prose").textContent(), /没有取得并完整审核 ISO 标准原文/);
    await page.goto(url + "#c17");
    await page.waitForFunction(() => document.getElementById("c17").open);
    assert.equal(await page.locator("#c17 .artwork img").count(), 3);
    for (const anchor of ["making-weave", "making-sample", "making-zine", "making-handmade",
                         "making-repair-goals", "making-kintsugi", "making-conservation", "making-repair-choice"]) {
      await page.locator("#c17 a[href='#" + anchor + "']").click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c17 .prose").isVisible());
    }
    for (const evidence of ["f28", "f29"]) {
      await page.locator("#c17 a[href='#" + evidence + "']").first().click();
      await page.waitForFunction(id => document.getElementById(id).open, evidence);
      await page.locator("#" + evidence + " a[href='#c17']").click();
      assert.equal(new URL(page.url()).hash, "#c17");
    }
    await page.locator("#c17 a[href='#f68']").click();
    await page.waitForFunction(() => document.getElementById("f68").open);
    assert.match(await page.locator("#f68 .prose").textContent(), /黄铜粉替代金粉/);
    assert.match(await page.locator("#f68 .prose").textContent(), /私人碗，而非馆藏/);
    await page.locator("#chapter-query").fill("不存在的修补XYZ");
    await page.locator("#f68 a[href='#making-conservation']").click();
    await page.waitForFunction(() => document.getElementById("c17").open &&
      !document.getElementById("c17").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#making-conservation");
    await page.locator("#c17 a[href='#b07']").click();
    await page.waitForFunction(() => document.getElementById("research-content").open);
    await page.locator("#research-content a[href='#n07']").click();
    await page.waitForFunction(() => document.getElementById("n07").open);
    assert.match(await page.locator("#n07 .prose").textContent(), /不是长期幸福或整个制作过程的愉快程度/);
    await page.goto(url + "#c18");
    await page.waitForFunction(() => document.getElementById("c18").open);
    for (const anchor of ["celebration-calendar", "celebration-repetition",
                          "celebration-magi", "celebration-generosity",
                          "celebration-objection", "celebration-top"]) {
      await page.locator(`#c18 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c18 .prose").isVisible());
    }
    const magiFold = page.locator("#c18 .prose details");
    assert.equal(await magiFold.count(), 1);
    assert.equal(await magiFold.evaluate(el => el.open), false);
    await magiFold.locator("summary").click();
    assert.equal(await magiFold.evaluate(el => el.open), true);
    assert.match(await magiFold.textContent(), /自己卖掉了金表来买发梳/);
    await magiFold.locator("summary").click();
    for (const id of ["f44", "f45"]) {
      await page.locator(`#c18 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c18']`).last().click();
      assert(await page.locator("#c18 .prose").isVisible());
    }
    await page.locator("#c18 a[href='#n08']").click();
    await page.waitForFunction(() => document.getElementById("n08").open);
    assert.match(await page.locator("#n08 .prose").textContent(), /实际享受的交互 F < 1/);
    await page.locator("#chapter-query").fill("C19");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c19");
    await page.waitForFunction(() => document.getElementById("c19").open);
    assert.match(await page.locator("#c19 .prose").textContent(), /输赢与选择质量，可以分开看/);
    const gameImage = page.locator("#c19 .artwork img");
    await gameImage.scrollIntoViewIfNeeded();
    await decodeImage(gameImage);
    assert.equal(await gameImage.evaluate(img => img.naturalWidth), 880);
    assert.equal(await page.locator("#c19 .prose table").count(), 2);
    for (const anchor of ["games-othello", "games-hanabi", "games-uncertainty",
                          "games-chosen-rules", "games-delegation"]) {
      await page.locator(`#c19 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c19 .prose").isVisible());
    }
    for (const id of ["f42", "f43"]) {
      await page.locator(`#c19 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c19']`).click();
      await page.waitForFunction(() => document.getElementById("c19").open);
    }
    await page.locator("#c19 a[href='#f09']").click();
    await page.waitForFunction(() => document.getElementById("f09").open);
    await page.goto(url + "#c19");
    await page.locator("#c19 a[href='#n09']").click();
    await page.waitForFunction(() => document.getElementById("n09").open);
    assert.match(await page.locator("#n09 .prose").textContent(), /不是 38,935 人都完成三轮/);
    await page.goto(url + "#c20");
    await page.waitForFunction(() => document.getElementById("c20").open);
    assert.equal(await page.locator("#c20 .artwork img").count(), 3);
    for (const anchor of ["photo-viewpoint", "photo-duration", "photo-sequence", "photo-audience"]) {
      await page.locator(`#c20 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c20 .prose").isVisible());
    }
    for (const image of await page.locator("#c20 .artwork img").all().then(images => images.slice(0, 2))) {
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), 880);
      assert.match(await image.getAttribute("src"), /^data:image\/png;base64,/);
      assert((await image.getAttribute("alt")).length > 40);
    }
    for (const anchor of ["photo-cyanotype-object", "photo-selective-truth"]) {
      await page.locator(`#c20 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
    }
    const cyanotypeImage = page.locator("#c20 .artwork img").nth(2);
    await cyanotypeImage.scrollIntoViewIfNeeded();
    await decodeImage(cyanotypeImage);
    assert.deepEqual(await cyanotypeImage.evaluate(img => [img.naturalWidth, img.naturalHeight]), [720, 882]);
    assert.match(await cyanotypeImage.getAttribute("src"), /^data:image\/jpeg;base64,/);
    assert.match(await cyanotypeImage.getAttribute("alt"), /不是植物原色照片/);
    await page.locator("#c20 a[href='#f67']").first().click();
    await page.waitForFunction(() => document.getElementById("f67").open);
    assert.match(await page.locator("#f67 .prose").textContent(), /不提供制作教程/);
    await page.locator("#chapter-query").fill("不存在的蓝晒XYZ");
    await page.locator("#f67 a[href='#photo-selective-truth']").click();
    await page.waitForFunction(() => document.getElementById("c20").open &&
      !document.getElementById("c20").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#photo-selective-truth");
    await page.locator("#c20 a[href='#f34']").first().click();
    await page.waitForFunction(() => document.getElementById("f34").open);
    assert.match(await page.locator("#f34 .prose").textContent(), /没有运行/);
    await page.locator("#f34 a[href='#c20']").click();
    await page.waitForFunction(() => document.getElementById("c20").open);
    await page.locator("#c20 a[href='#f10']").first().click();
    await page.waitForFunction(() => document.getElementById("f10").open);
    await page.goto(url + "#c20");
    await page.locator("#c20 a[href='#n10']").click();
    await page.waitForFunction(() => document.getElementById("n10").open);
    assert.match(await page.locator("#n10 .prose").textContent(), /p = .058/);
    await page.locator("#chapter-query").fill("C21");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c21");
    await page.waitForFunction(() => document.getElementById("c21").open);
    assert.match(await page.locator("#c21 .prose").textContent(), /让事情发生，和让发生的过程更舒服/);
    await page.locator("#c21 a[href='#n11']").click();
    await page.waitForFunction(() => document.getElementById("n11").open);
    assert.match(await page.locator("#n11 .prose").textContent(), /49.3%/);
    assert.match(await page.locator("#n11 .prose").textContent(), /p = .06/);
    await page.goto(url + "#c22");
    await page.waitForFunction(() => document.getElementById("c22").open);
    assert.match(await page.locator("#c22 .prose").textContent(), /奥斯汀的第一句话/);
    assert.equal(await page.locator("#c22 .prose table").count(), 2);
    await page.locator("#c22 a[href='#f11']").click();
    await page.waitForFunction(() => document.getElementById("f11").open);
    assert.match(await page.locator("#f11 .prose").textContent(), /社区整理的原作转录/);
    await page.locator("#chapter-query").fill("C23");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c23");
    await page.waitForFunction(() => document.getElementById("c23").open);
    assert.equal(await page.locator("#c23 .prose table").count(), 3);
    assert.match(await page.locator("#c23 .prose").textContent(), /310 分钟/);
    for (const anchor of ["travel-once", "travel-guide", "travel-authenticity", "travel-forster"]) {
      await page.locator(`#c23 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c23 .prose").isVisible());
    }
    assert.equal(await page.locator("#c23 .prose details").evaluate(e => e.open), false);
    await page.locator("#c23 .prose details > summary").click();
    assert.equal(await page.locator("#c23 .prose details").evaluate(e => e.open), true);
    assert.match(await page.locator("#c23 .prose details").textContent(), /Miss Lavish/);
    await page.locator("#c23 a[href='#f58']").first().click();
    await page.waitForFunction(() => document.getElementById("f58").open);
    assert.equal(await page.locator("#f58 .prose details").evaluate(e => e.open), false);
    await page.locator("#f58 .prose details > summary").click();
    assert.match(await page.locator("#f58 .prose details").textContent(), /不是福斯特本人/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f58 a[href='#travel-forster']").first().click();
    await page.waitForFunction(() => document.getElementById("c23").open &&
      !document.getElementById("c23").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#travel-forster");
    await page.locator("#c23 a[href='#n12']").click();
    await page.waitForFunction(() => document.getElementById("n12").open);
    assert.match(await page.locator("#n12 .prose").textContent(), /不是把同一批人逐日追踪八周/);
    await page.goto(url + "#c23");
    await page.locator("#c23 a[href='#f12']").click();
    await page.waitForFunction(() => document.getElementById("f12").open);
    assert.match(await page.locator("#f12 .prose").textContent(), /不能被拼接成该来源支持随意离队/);
    await page.goto(url + "#c24");
    await page.waitForFunction(() => document.getElementById("c24").open);
    assert.match(await page.locator("#c24 .prose").textContent(), /我家的书架已经很有文化了/);
    await page.locator("#c24 a[href='#n13']").click();
    await page.waitForFunction(() => document.getElementById("n13").open);
    assert.match(await page.locator("#n13 .prose").textContent(), /方法报 73 名大学生/);
    await page.locator("#chapter-query").fill("C25");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c25");
    await page.waitForFunction(() => document.getElementById("c25").open);
    assert.equal(await page.locator("#c25 .artwork img").count(), 5);
    for (const image of await page.locator("#c25 .artwork img").all()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.ok(await image.evaluate(img => img.naturalWidth > 0 && img.alt.length > 30));
    }
    await page.locator("#c25 a[href='#art-sculpture-recognition']").first().click();
    assert.equal(new URL(page.url()).hash, "#art-sculpture-recognition");
    assert.match(await page.locator("#c25 .prose").textContent(), /雕塑的部件选择，不能替真实的人定义身体价值/);
    await page.locator("#c25 a[href='#f77']").first().click();
    await page.waitForFunction(() => document.getElementById("f77").open);
    assert.match(await page.locator("#f77 .prose").textContent(), /2014-01-17/);
    assert.match(await page.locator("#f77 .prose").textContent(), /2015-01-17/);
    await page.locator("#f77 a[href='#art-sculpture-recognition']").first().click();
    await page.waitForFunction(() => document.getElementById("c25").open);
    await page.locator("#c25 a[href='#f13']").first().click();
    await page.waitForFunction(() => document.getElementById("f13").open);
    assert.match(await page.locator("#f13 .prose").textContent(), /1926.417/);
    await page.goto(url + "#c25");
    assert.equal(await page.locator("#c25 .prose table").count(), 3);
    for (const anchor of ["art-letters-and-versions", "art-material-history",
                          "art-traces-and-meaning", "art-knowledge-and-pleasure"]) {
      await page.locator(`#c25 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c25 .prose").isVisible());
    }
    for (const [id, anchor, phrase] of [
      ["f54", "art-letters-and-versions", /两封信的日期来自编辑判断/],
      ["f55", "art-material-history", /不是完整实验报告/]
    ]) {
      await page.locator(`#c25 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      assert.match(await page.locator(`#${id} .prose`).textContent(), phrase);
      await page.locator(`#${id} a[href='#${anchor}']`).last().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c25 .prose").isVisible());
    }
    await page.goto(url + "#c13");
    await page.waitForFunction(() => document.getElementById("c13").open);
    const theatreImage = page.locator("#c13 .artwork img");
    await theatreImage.scrollIntoViewIfNeeded();
    await decodeImage(theatreImage);
    assert.equal(await theatreImage.evaluate(img => img.naturalWidth), 880);
    assert.equal(await page.locator("#c13 .prose table").count(), 3);
    assert.match(await page.locator("#c13 .prose table").nth(0).textContent(), /选场次或位置时优先确认什么/);
    assert.match(await page.locator("#c13 .prose table").nth(1).textContent(), /一项有边界的共同决定/);
    assert.match(await page.locator("#c13 .prose table").nth(2).textContent(), /镜框式：通过框架面向舞台/);
    for (const anchor of ["live-medium", "live-space", "live-convention",
                          "live-anticipation", "live-understanding"]) {
      await page.locator(`#c13 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c13 .prose").isVisible());
    }
    for (const id of ["f40", "f41"]) {
      await page.locator(`#c13 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c13']`).click();
      await page.waitForFunction(() => document.getElementById("c13").open);
    }
    await page.goto(url + "#c26");
    await page.waitForFunction(() => document.getElementById("c26").open);
    assert.match(await page.locator("#c26 > summary").textContent(), /永远差最后一件/);
    assert.equal(await page.locator("#c26 .artwork img").count(), 2);
    assert.equal(await page.locator("#c26 .prose table").count(), 3);
    for (const image of await page.locator("#c26 .artwork img").all()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), 599);
      assert((await image.getAttribute("alt")).length > 50);
    }
    for (const anchor of ["collecting-crosses", "collecting-layers", "collecting-digital",
                          "collecting-return", "collecting-abundance"]) {
      await page.locator(`#c26 a[href='#${anchor}']`).click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert(await page.locator("#c26 .prose").isVisible());
    }
    for (const id of ["f38", "f39"]) {
      await page.locator(`#c26 a[href='#${id}']`).first().click();
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator(`#${id} a[href='#c26']`).click();
      await page.waitForFunction(() => document.getElementById("c26").open);
    }
    await page.locator("#c26 a[href='#f14']").first().click();
    await page.waitForFunction(() => document.getElementById("f14").open);
    assert.match(await page.locator("#f14 .prose").textContent(), /不是藏品鉴定/);
    await page.locator("#chapter-query").fill("C27");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c27");
    await page.waitForFunction(() => document.getElementById("c27").open);
    assert.equal(await page.locator("#c27 .prose table").count(), 2);
    assert.match(await page.locator("#c27 .prose").textContent(), /一段动作，不只由姿势组成/);
    await page.locator("#c27 a[href='#f17']").first().click();
    await page.waitForFunction(() => document.getElementById("f17").open);
    assert.match(await page.locator("#f17 .prose").textContent(), /没有观看并核验完整演出/);
    await page.goto(url + "#c28");
    await page.waitForFunction(() => document.getElementById("c28").open);
    assert.equal(await page.locator("#c28 .prose table").count(), 3);
    assert.match(await page.locator("#c28 .prose table").nth(2).textContent(), /48∶80/);
    await page.locator("#c28 a[href='#sport-tennis']").click();
    assert.equal(new URL(page.url()).hash, "#sport-tennis");
    await page.locator("#c28 a[href='#f64']").first().click();
    await page.waitForFunction(() => document.getElementById("f64").open);
    assert.match(await page.locator("#f64 .prose").textContent(), /128 分、26 局、3 盘/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f64 a[href='#sport-tennis']").first().click();
    await page.waitForFunction(() => document.getElementById("c28").open &&
      !document.getElementById("c28").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#sport-tennis");
    const offside = page.locator("#c28 .artwork img");
    await offside.scrollIntoViewIfNeeded();
    await decodeImage(offside);
    assert.ok(await offside.evaluate(img => img.naturalWidth > 0 && img.alt.length > 30));
    assert.ok(await offside.evaluate(img => img.getBoundingClientRect().width <= 440));
    await page.screenshot({path: "/tmp/enjoythemoment-sport-desktop.png", fullPage: false});
    await page.locator("#c28 a[href='#f18']").first().click();
    await page.waitForFunction(() => document.getElementById("f18").open);
    assert.match(await page.locator("#f18 .prose").textContent(), /位置本身不是犯规/);
    await page.goto(url + "#c28");
    await page.locator("#c28 a[href='#f19']").first().click();
    await page.waitForFunction(() => document.getElementById("f19").open);
    assert.match(await page.locator("#f19 .prose").textContent(), /生效日尚未到来/);
    await page.locator("#chapter-query").fill("C29");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c29");
    await page.waitForFunction(() => document.getElementById("c29").open);
    assert.equal(await page.locator("#c29 .prose table").count(), 3);
    for (const anchor of ["moon-rotation", "moon-day-and-night", "moon-changing-view",
                          "moon-knowledge-and-wonder"]) {
      await page.locator(`#c29 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, "#" + anchor);
      assert(await page.locator("#c29 .prose").isVisible());
    }
    const moonImage = page.locator("#c29 .prose img");
    await moonImage.scrollIntoViewIfNeeded();
    await decodeImage(moonImage);
    assert(await moonImage.evaluate(img => img.naturalWidth === 720 && img.alt.includes("1右")));
    await page.locator("#c29 a[href='#f56']").first().click();
    await page.waitForFunction(() => document.getElementById("f56").open);
    assert.match(await page.locator("#f56 .prose").textContent(), /不把静态占位当成2026年的有效星历/);
    await page.locator("#f56 a[href='#moon-rotation']").last().click();
    assert.equal(new URL(page.url()).hash, "#moon-rotation");
    assert.match(await page.locator("#c29 .prose").textContent(), /多数纬度/);
    await page.locator("#c29 .prose table").first().scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-sky-desktop.png", fullPage: false});
    await page.locator("#c29 a[href='#f21']").first().click();
    await page.waitForFunction(() => document.getElementById("f21").open);
    assert.match(await page.locator("#f21 .prose").textContent(), /没有教读者选购、安装、自制或检验太阳滤镜/);
    await page.goto(url + "#c30");
    await page.waitForFunction(() => document.getElementById("c30").open);
    assert.equal(await page.locator("#chapter-query").inputValue(), "");
    assert.equal(await page.locator("#c30 .prose table").count(), 2);
    assert.match(await page.locator("#c30 .prose").textContent(), /不是你所在城市的鸟类名录/);
    await page.locator("#c30 a[href='#f22']").first().click();
    await page.waitForFunction(() => document.getElementById("f22").open);
    assert.match(await page.locator("#f22 .prose").textContent(), /没有逐张目视核验照片/);
    await page.goto(url + "#c30");
    await page.locator("#c30 a[href='#f23']").first().click();
    await page.waitForFunction(() => document.getElementById("f23").open);
    assert.match(await page.locator("#f23 .prose").textContent(), /圈养鸟类另有边界/);
    await page.locator("#chapter-query").fill("C31");
    assert.equal(await page.locator(".chapter-intro:visible").count(), 1);
    await page.goto(url + "#c31");
    await page.waitForFunction(() => document.getElementById("c31").open);
    const fearSpoiler = page.locator("#c31 .prose details");
    assert.equal(await fearSpoiler.count(), 1);
    assert.equal(await fearSpoiler.getAttribute("open"), null);
    assert.match(await fearSpoiler.locator("summary").textContent(), /重大剧透/);
    assert.equal(await fearSpoiler.locator("p").first().isVisible(), false);
    await fearSpoiler.locator("summary").focus();
    await page.keyboard.press("Enter");
    assert(await fearSpoiler.locator("p").first().isVisible());
    assert.match(await fearSpoiler.textContent(), /没有直接交代第三个愿望的具体措辞/);
    await fearSpoiler.locator("p").first().scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-fear-desktop.png", fullPage: false});
    await fearSpoiler.locator("summary").click();
    assert.equal(await page.locator("#c31 .prose table").count(), 2);
    await page.locator("#c31 a[href='#fear-three-explanations']").click();
    assert.equal(new URL(page.url()).hash, "#fear-three-explanations");
    await page.locator("#c31 a[href='#f61']").first().click();
    await page.waitForFunction(() => document.getElementById("f61").open);
    assert.match(await page.locator("#f61 .prose").textContent(), /完整核读正文 Tr 1–28/);
    assert.match(await page.locator("#f61 .prose").textContent(), /没有独立读取迪博或丰特奈尔原作/);
    await page.locator("#chapter-query").fill("不存在的章节XYZ");
    await page.locator("#f61 a[href='#fear-conversion-limit']").click();
    await page.waitForFunction(() => document.getElementById("c31").open &&
      !document.getElementById("c31").hidden && document.getElementById("chapter-query").value === "");
    assert.equal(new URL(page.url()).hash, "#fear-conversion-limit");
    assert.equal(await fearSpoiler.getAttribute("open"), null);
    await page.locator("#c31 a[href='#n15']").first().click();
    await page.waitForFunction(() => document.getElementById("n15").open);
    assert.match(await page.locator("#n15 .prose").textContent(), /p = \.564/);
    await page.goto(url + "#c31");
    await page.locator("#c31 a[href='#f24']").first().click();
    await page.waitForFunction(() => document.getElementById("f24").open);
    assert.equal(await page.locator("#f24 .prose details").getAttribute("open"), null);
    assert.equal(await page.locator("#f24 .prose details p").first().isVisible(), false);
    await page.goto(url + "#c32");
    await page.waitForFunction(() => document.getElementById("c32").open);
    assert.equal(await page.locator("#chapter-query").inputValue(), "");
    const hints = page.locator("#c32 .prose details");
    assert.equal(await hints.count(), 8);
    for (const hint of await hints.all()) assert.equal(await hint.getAttribute("open"), null);
    await hints.nth(0).locator("summary").click();
    assert(await hints.nth(0).locator("p").first().isVisible());
    assert.equal(await hints.nth(2).locator("p").first().isVisible(), false);
    await hints.nth(1).locator("summary").click();
    assert.equal(await hints.nth(2).locator("p").first().isVisible(), false);
    await hints.nth(2).locator("summary").click();
    assert.match(await hints.nth(2).textContent(), /伞、地图、船、月亮/);
    assert.equal(await hints.nth(3).locator("p").first().isVisible(), false);
    for (const anchor of ["puzzle-cards", "puzzle-roads", "puzzle-invariants",
                          "puzzle-rule-change", "puzzle-knowing"]) {
      await page.locator(`#c32 a[href='#${anchor}']`).first().click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
    }
    const roadImage = page.locator("#c32 .artwork img");
    await roadImage.scrollIntoViewIfNeeded();
    await decodeImage(roadImage);
    assert.equal(await roadImage.evaluate(img => img.naturalWidth), 880);
    for (const [index, phrase] of [[4, "起点和终点"], [5, "B → A → C → B → D → C"],
                                   [6, "00000 → 11000"], [7, "8个可达状态"]]) {
      assert.equal(await hints.nth(index).evaluate(el => el.open), false);
      await hints.nth(index).locator("summary").click();
      assert.match(await hints.nth(index).textContent(), new RegExp(phrase));
      await hints.nth(index).locator("summary").click();
    }
    await page.locator("#c32 a[href='#f46']").first().click();
    await page.waitForFunction(() => document.getElementById("f46").open);
    await page.locator("#f46 a[href='#c32']").last().click();
    await page.locator("#c32 a[href='#n16']").first().click();
    await page.waitForFunction(() => document.getElementById("n16").open);
    assert.match(await page.locator("#n16 .prose").textContent(), /不是所有顿悟中有 37%/);
    await page.locator("#essay-query").fill("E10");
    assert.equal(await page.locator(".argument:visible").count(), 1);
    await page.goto(url + "#e10");
    await page.waitForFunction(() => document.getElementById("e10").open);
    assert.equal(await page.locator("#e10 .prose table").count(), 3);
    assert.match(await page.locator("#e10 .prose").textContent(), /开始、继续、再次回来/);
    await page.locator("#e10 .prose table").first().scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-attention-desktop.png", fullPage: false});
    await page.locator("#e10 a[href='#b14']").first().click();
    await page.waitForFunction(() => document.getElementById("research-content").open);
    assert.equal(new URL(page.url()).hash, "#b14");
    assert.match(await page.locator("#b14 + h3").textContent(), /暗黑模式的存在/);
    assert(await page.locator("#b14 + h3").isVisible());
    await page.goto(url + "#e10");
    await page.locator("#e10 a[href='#n14']").first().click();
    await page.waitForFunction(() => document.getElementById("n14").open);
    assert.match(await page.locator("#n14 .prose").textContent(), /不是对 11,286 名消费者的实验/);
    await page.goto(url + "#e10");
    await page.locator("#e10 a[href='#f20']").first().click();
    await page.waitForFunction(() => document.getElementById("f20").open);
    assert.match(await page.locator("#f20 .prose").textContent(), /六至九个页面/);
    await page.goto(url + "#digital-chosen-limits");
    await page.waitForFunction(() => document.getElementById("e10").open);
    assert.match(await page.locator("#e10 .prose").textContent(), /同一个晚上另一种快乐/);
    await page.locator("#e10 a[href='#b28']").first().click();
    await page.waitForFunction(() => document.getElementById("research-content").open);
    assert.equal(new URL(page.url()).hash, "#b28");
    await page.locator("#research a[href='#n28']").first().click();
    await page.waitForFunction(() => document.getElementById("n28").open);
    assert.equal(await page.locator("#n28 .prose table").count(), 2);
    assert.match(await page.locator("#n28 .prose").textContent(), /内容是HTML而非PDF/);
    assert.match(await page.locator("#n28 .prose").textContent(), /其他手机应用日均增加约12分钟/);
    await page.locator("#essay-query").fill("不存在的长文XYZ");
    await page.locator("#n28 a[href='#digital-experiment']").click();
    await page.waitForFunction(() => document.getElementById("e10").open &&
      !document.getElementById("e10").hidden && document.getElementById("essay-query").value === "");
    assert.equal(new URL(page.url()).hash, "#digital-experiment");
    await page.locator("#essay-query").fill("E08");
    assert.equal(await page.locator(".argument:visible").count(), 1);
    await page.locator("#essay-query").fill("没有这个论点887765");
    assert.equal(await page.locator(".argument:visible").count(), 0);
    await page.goto(url + "#e07");
    await page.waitForFunction(() => document.getElementById("e07").open);
    assert.equal(await page.locator("#essay-query").inputValue(), "");
    await page.locator("#guide-query").fill("P010");
    assert.equal(await page.locator(".playbook:visible").count(), 1);
    await page.goto(url + "#p010");
    await page.waitForFunction(() => document.getElementById("p010").open);
    assert.equal(await page.locator("#p010 .prose details").count(), 4);
    assert.equal(await page.locator("#p010 .prose details[open]").count(), 0);
    await page.locator("#p010 .prose details > summary").first().click();
    assert.equal(await page.locator("#p010 .prose details[open]").count(), 1);
    await page.locator("#guide-query").fill("不存在的玩法887");
    await page.goto(url + "#p001");
    await page.waitForFunction(() => document.getElementById("p001").open);
    assert.equal(await page.locator("#guide-query").inputValue(), "");
    await page.goto(url + "#n04");
    await page.waitForFunction(() => document.getElementById("n04").open);
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
    for (const id of ["c15", "f35", "f36"]) {
      await page.goto(url + "#" + id);
      await page.waitForFunction(id => document.getElementById(id).open, id);
      for (const [i, table] of (await page.locator(`#${id} .prose table`).all()).entries()) {
        await table.scrollIntoViewIfNeeded();
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert(await table.evaluate(el => el.getBoundingClientRect().width <= 350));
        await page.screenshot({path: `/tmp/enjoythemoment-public-life-${id}-${i}-mobile.png`, fullPage: false});
      }
    }
    await page.goto(url + "#c20");
    await page.waitForFunction(() => document.getElementById("c20").open);
    for (const [i, image] of (await page.locator("#c20 .artwork img").all()).entries()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert(await image.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
      if (i < 2) assert(await image.evaluate(img => 20 * (img.getBoundingClientRect().width - 2) / 440 >= 15));
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-photography-" + i + "-mobile.png", fullPage: false});
    }
    for (const table of await page.locator("#c20 .prose table").all()) {
      await table.scrollIntoViewIfNeeded();
      assert(await table.evaluate(el => el.getBoundingClientRect().width <= 350));
    }
    await page.goto(url + "#f34");
    await page.waitForFunction(() => document.getElementById("f34").open);
    await page.locator("#f34 table").scrollIntoViewIfNeeded();
    assert(await page.locator("#f34 table").evaluate(el => el.getBoundingClientRect().width <= 350));
    await page.goto(url + "#c34");
    await page.waitForFunction(() => document.getElementById("c34").open);
    for (const [i, table] of (await page.locator("#c34 .prose table").all()).entries()) {
      await table.scrollIntoViewIfNeeded();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert(await table.evaluate(el => el.getBoundingClientRect().width <= 350));
      await page.screenshot({path: "/tmp/enjoythemoment-stories-" + i + "-mobile.png", fullPage: false});
    }
    await page.goto(url + "#c33");
    await page.waitForFunction(() => document.getElementById("c33").open);
    for (const [i, table] of (await page.locator("#c33 .prose table").all()).entries()) {
      await table.scrollIntoViewIfNeeded();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert(await table.evaluate(el => el.getBoundingClientRect().width <= 350));
      await page.screenshot({path: "/tmp/enjoythemoment-singing-" + i + "-mobile.png", fullPage: false});
    }
    await page.goto(url + "#c17");
    await page.waitForFunction(() => document.getElementById("c17").open);
    const makingImages = await page.locator("#c17 .artwork img").all();
    for (const [i, image] of makingImages.entries()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), 880);
      assert(await image.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
      assert(await image.evaluate(img => 20 * (img.getBoundingClientRect().width - 2) / 440 >= 15));
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-making-" + i + "-mobile.png", fullPage: false});
    }
    await page.goto(url + "#e11");
    await page.waitForFunction(() => document.getElementById("e11").open);
    await page.locator("#e11 .prose table").first().scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: "/tmp/enjoythemoment-pleasure-reality-mobile.png", fullPage: false});
    await page.goto(url + "#e10");
    await page.waitForFunction(() => document.getElementById("e10").open);
    await page.locator("#e10 .prose table").first().scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: "/tmp/enjoythemoment-attention-mobile.png", fullPage: false});
    await page.goto(url);
    await page.reload();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.goto(url + "#e04");
    await page.waitForFunction(() => document.getElementById("e04").open);
    assert.equal(await page.locator("#e04 .prose h3").count(), 4);
    for (const anchor of ["purchase-purpose", "purchase-choice",
                         "purchase-agency", "purchase-judgement",
                         "purchase-moving-rules"]) {
      const heading = page.locator("#" + anchor + " + :is(h3,h5)");
      assert.equal(await heading.count(), 1);
      assert(await heading.evaluate(el =>
        parseFloat(getComputedStyle(el).fontSize) >=
        parseFloat(getComputedStyle(el.closest(".prose")).fontSize)));
    }
    await page.locator("#e04").evaluate(el => el.scrollIntoView({behavior: "instant", block: "start"}));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: "/tmp/enjoythemoment-essay-mobile.png", fullPage: false});
    await page.goto(url + "#c25");
    await page.waitForFunction(() => document.getElementById("c25").open);
    const artImage = page.locator("#c25 .artwork img").first();
    await artImage.scrollIntoViewIfNeeded();
    await decodeImage(artImage);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert(await artImage.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
    await page.screenshot({path: "/tmp/enjoythemoment-art-mobile.png", fullPage: false});
    for (const id of ["c11", "c12"]) {
      await page.goto(url + "#" + id);
      await page.waitForFunction(id => document.getElementById(id).open, id);
      const image = page.locator("#" + id + " .artwork img").first();
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert(await image.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-" + id + "-mobile.png", fullPage: false});
    }
    for (const id of ["c14", "c16"]) {
      await page.goto(url + "#" + id);
      const image = page.locator("#" + id + " .artwork img").first();
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert(await image.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-" + id + "-detail-mobile.png", fullPage: false});
    }
    await page.locator("#c12 .prose details > summary").click();
    const ending = page.locator("#c12 .prose details img");
    await ending.scrollIntoViewIfNeeded();
    await decodeImage(ending);
    await page.screenshot({path: "/tmp/enjoythemoment-film-spoiler-mobile.png", fullPage: false});
    for (const id of ["c27", "c28", "c29", "c30"]) {
      await page.goto(url + "#" + id);
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator("#" + id + " .prose table").first().scrollIntoViewIfNeeded();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-" + id + "-mobile.png", fullPage: false});
    }
    await page.goto(url + "#c30");
    await page.locator("#c30 .prose table").nth(1).scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-birds-mobile.png", fullPage: false});
    await page.goto(url + "#c29");
    await page.locator("#c29 .prose table").first().scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-sky-mobile.png", fullPage: false});
    for (const id of ["c31", "c32"]) {
      await page.goto(url + "#" + id);
      await page.waitForFunction(id => document.getElementById(id).open, id);
      await page.locator("#" + id + " .prose table").first().scrollIntoViewIfNeeded();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path: "/tmp/enjoythemoment-" + id + "-mobile.png", fullPage: false});
    }
    await page.goto(url + "#c32");
    await page.locator("#c32 .prose details").nth(2).scrollIntoViewIfNeeded();
    await page.screenshot({path: "/tmp/enjoythemoment-puzzle-mobile.png", fullPage: false});
    const mobileOffside = page.locator("#c28 .artwork img");
    await mobileOffside.scrollIntoViewIfNeeded();
    await decodeImage(mobileOffside);
    assert(await mobileOffside.evaluate(img => img.getBoundingClientRect().right <= innerWidth));
    // This portrait diagram uses a 440-unit canvas and 22-unit minimum text.
    // Guard against returning to the illegible wide version; visual QA is still required.
    assert(await mobileOffside.evaluate(img => 22 * (img.getBoundingClientRect().width - 2) / 440 >= 16));
    await page.screenshot({path: "/tmp/enjoythemoment-offside-mobile.png", fullPage: false});
    await page.goto(url);
    await page.reload();
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
    assert.equal(await staticPage.locator("#essay-search-label").isVisible(), false);
    await staticPage.locator("#e07 > summary").click();
    assert.equal(await staticPage.locator("#e07 .prose").isVisible(), true);
    await staticPage.locator("#e10 > summary").click();
    assert.equal(await staticPage.locator("#e10 .prose").isVisible(), true);
    assert.match(await staticPage.locator("#e10 .prose").textContent(), /不是市场报价/);
    await staticPage.locator("#e11 > summary").click();
    assert.equal(await staticPage.locator("#e11 .prose").isVisible(), true);
    assert.match(await staticPage.locator("#e11 .prose").textContent(), /不是直接核读诺齐克原书/);
    await staticPage.locator("#f27 > summary").click();
    assert.equal(await staticPage.locator("#f27 .prose").isVisible(), true);
    assert.equal(await staticPage.locator("#f27 a[href='#e11']").count(), 1);
    await staticPage.locator("#c17 > summary").click();
    assert.equal(await staticPage.locator("#c17 .prose").isVisible(), true);
    for (const image of await staticPage.locator("#c17 .artwork img").all()) {
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), 880);
    }
    await staticPage.locator("#c15 > summary").click();
    assert.match(await staticPage.locator("#c15 .prose").textContent(), /18 人次/);
    await staticPage.locator("#f35 > summary").click();
    assert.match(await staticPage.locator("#f35 .prose").textContent(), /小区域例外/);
    await staticPage.locator("#f36 > summary").click();
    assert.equal(await staticPage.locator("#f36 table tbody tr").count(), 3);
    await staticPage.locator("#c20 > summary").click();
    for (const [i, image] of (await staticPage.locator("#c20 .artwork img").all()).entries()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.equal(await image.evaluate(img => img.naturalWidth), i < 2 ? 880 : 720);
    }
    await staticPage.locator("#f34 > summary").click();
    assert.match(await staticPage.locator("#f34 .prose").textContent(), /沿光轴/);
    await staticPage.locator("#j001 > summary").click();
    assert.equal(await staticPage.locator("#j001 .card-body").isVisible(), true);
    await staticPage.locator("#c25 > summary").click();
    assert.equal(await staticPage.locator("#c25 .artwork img").count(), 5);
    await staticPage.locator("#c25 .artwork img").first().scrollIntoViewIfNeeded();
    assert(await staticPage.locator("#c25 .artwork img").first().evaluate(img => img.complete && img.naturalWidth > 0));
    await staticPage.locator("#c12 > summary").click();
    assert.equal(await staticPage.locator("#c12 .prose details img").isVisible(), false);
    await staticPage.locator("#c12 .prose details > summary").click();
    await staticPage.locator("#c12 .prose details img").scrollIntoViewIfNeeded();
    await decodeImage(staticPage.locator("#c12 .prose details img"));
    assert(await staticPage.locator("#c12 .prose details img").isVisible());
    await staticPage.locator("#c27 > summary").click();
    assert.match(await staticPage.locator("#c27 .prose").textContent(), /不加难|四格|四个问题/);
    await staticPage.locator("#c28 > summary").click();
    assert.equal(await staticPage.locator("#c28 .prose table").count(), 3);
    assert.match(await staticPage.locator("#c28 .prose table").nth(2).textContent(), /12∶14/);
    await staticPage.locator("#c28 .artwork img").scrollIntoViewIfNeeded();
    await decodeImage(staticPage.locator("#c28 .artwork img"));
    assert(await staticPage.locator("#c28 .artwork img").isVisible());
    for (const id of ["c14", "c16"]) {
      await staticPage.locator("#" + id + " > summary").click();
      const image = staticPage.locator("#" + id + " .artwork img").first();
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert(await image.isVisible());
    }
    for (const id of ["c29", "c30"]) {
      await staticPage.locator(`#${id} > summary`).click();
      assert(await staticPage.locator(`#${id} .prose`).isVisible());
      assert.equal(await staticPage.locator(`#${id} .prose table`).count(), id === "c29" ? 3 : 2);
    }
    await staticPage.locator("#c29 .prose img").scrollIntoViewIfNeeded();
    await decodeImage(staticPage.locator("#c29 .prose img"));
    assert(await staticPage.locator("#c29 .prose img").isVisible());
    await staticPage.locator("#c31 > summary").click();
    assert.equal(await staticPage.locator("#c31 .prose details p").first().isVisible(), false);
    await staticPage.locator("#c31 .prose details > summary").click();
    assert(await staticPage.locator("#c31 .prose details p").first().isVisible());
    await staticPage.locator("#c32 > summary").click();
    const staticHints = staticPage.locator("#c32 .prose details");
    assert.equal(await staticHints.count(), 8);
    await staticHints.nth(0).locator("summary").click();
    assert(await staticHints.nth(0).locator("p").first().isVisible());
    assert.equal(await staticHints.nth(2).locator("p").first().isVisible(), false);
    await staticPage.locator("#c32 .artwork img").scrollIntoViewIfNeeded();
    await decodeImage(staticPage.locator("#c32 .artwork img"));
    assert.equal(await staticHints.nth(6).locator("table").isVisible(), false);
    await staticHints.nth(6).locator("summary").click();
    assert(await staticHints.nth(6).locator("table").isVisible());
    await staticPage.locator("#c33 > summary").click();
    assert.equal(await staticPage.locator("#c33 .prose table").count(), 4);
    assert.match(await staticPage.locator("#c33 .prose").textContent(), /低八度本身也是移调的一种/);
    await staticPage.locator("#c34 > summary").click();
    assert.equal(await staticPage.locator("#c34 .prose table").count(), 5);
    assert.match(await staticPage.locator("#c34 .prose").textContent(), /11\/36/);
    assert.match(await staticPage.locator("#c34 .prose").textContent(), /钟箱已经在船上，离港窗口也已经关闭/);
    await staticPage.locator("#f65 > summary").click();
    assert.match(await staticPage.locator("#f65 .prose").textContent(), /不是随机模拟/);
    await staticPage.locator("#c24 > summary").click();
    const staticComicFold = staticPage.locator("#c24 .prose details");
    assert.equal(await staticComicFold.locator("p").first().isVisible(), false);
    await staticComicFold.locator("summary").click();
    assert(await staticComicFold.locator("p").first().isVisible());
    assert.equal(await staticPage.locator("#c24 .prose table").count(), 2);
    await staticPage.locator("#c26 > summary").click();
    assert.equal(await staticPage.locator("#c26 .prose table").count(), 3);
    assert.equal(await staticPage.locator("#c26 .artwork img").count(), 2);
    for (const image of await staticPage.locator("#c26 .artwork img").all()) {
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert(await image.isVisible());
    }
    await nojs.close();
    // Opening argument: readable without JS; evidence links must not become card validation.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const opening = await context.newPage();
      const failures = [], network = [];
      opening.on("pageerror", error => failures.push(error.message));
      opening.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await opening.goto(url + (javaScriptEnabled ? "#c01" : ""));
      if (!javaScriptEnabled) await opening.locator("#c01 > summary").click();
      assert.match(await opening.locator("#c01 .prose").textContent(), /兑换比例/);
      for (const anchor of ["today-voucher", "today-future", "today-not-redemption"]) {
        if (javaScriptEnabled) {
          await opening.locator(`#c01 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(opening.url()).hash, "#" + anchor);
        }
        await opening.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      const table = opening.locator("#c01 .prose table");
      assert.equal(await table.count(), 1);
      assert((await table.boundingBox()).width <= 350);
      if (javaScriptEnabled) {
        await opening.locator("#c01 a[href='#n17']").first().click();
        await opening.waitForFunction(() => document.getElementById("n17").open);
      } else {
        await opening.locator("#n17 > summary").click();
      }
      for (const selector of ["#c01 .prose", "#n17 .prose"]) {
        const shape = await opening.locator(selector).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, selector);
      }
      assert.match(await opening.locator("#n17 .prose").textContent(), /4.64/);
      if (javaScriptEnabled) {
        await opening.locator("#n17 a[href='#today-voucher']").last().click();
        assert.equal(new URL(opening.url()).hash, "#today-voucher");
        assert(await opening.locator("#c01 .prose").isVisible());
      }
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    // Aftertaste: a preference study must remain distinct from an activity effect.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const aftertaste = await context.newPage();
      const failures = [], network = [];
      aftertaste.on("pageerror", error => failures.push(error.message));
      aftertaste.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await aftertaste.goto(url + (javaScriptEnabled ? "#c10" : ""));
      if (!javaScriptEnabled) await aftertaste.locator("#c10 > summary").click();
      assert.match(await aftertaste.locator("#c10 .prose").textContent(), /回忆不是当下的敌人/);
      for (const anchor of ["aftertaste-three-questions", "aftertaste-preference", "aftertaste-story",
                           "aftertaste-gifts", "aftertaste-peak-boundary", "aftertaste-not-a-score"]) {
        if (javaScriptEnabled) {
          await aftertaste.locator(`#c10 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(aftertaste.url()).hash, "#" + anchor);
        }
        await aftertaste.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      assert.equal(await aftertaste.locator("#c10 .prose table").count(), 3);
      for (const table of await aftertaste.locator("#c10 .prose table").all()) {
        assert((await table.boundingBox()).width <= 350);
      }
      if (javaScriptEnabled) {
        await aftertaste.locator("#c10 a[href='#n18']").first().click();
        await aftertaste.waitForFunction(() => document.getElementById("n18").open);
      } else {
        await aftertaste.locator("#n18 > summary").click();
      }
      for (const selector of ["#c10 .prose", "#n18 .prose"]) {
        const shape = await aftertaste.locator(selector).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, selector);
      }
      assert.match(await aftertaste.locator("#n18 .prose").textContent(), /196 \/ 290/);
      if (javaScriptEnabled) {
        await aftertaste.locator("#n18 a[href='#aftertaste-preference']").last().click();
        assert.equal(new URL(aftertaste.url()).hash, "#aftertaste-preference");
        assert(await aftertaste.locator("#c10 .prose").isVisible());
      }
      for (const [id, anchor, phrase] of [
        ["n34", "aftertaste-gifts", /没有随机操纵事件边界/],
        ["n35", "aftertaste-peak-boundary", /不是观看时实时连续评分|没有观看时实时连续评分/]
      ]) {
        if (javaScriptEnabled) {
          await aftertaste.locator(`#c10 a[href='#${id}']`).first().click();
          await aftertaste.waitForFunction(id => document.getElementById(id).open, id);
        } else {
          await aftertaste.locator(`#${id} > summary`).click();
        }
        assert.match(await aftertaste.locator(`#${id} .prose`).textContent(), phrase);
        const shape = await aftertaste.locator(`#${id} .prose`).evaluate(
          el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, id);
        if (javaScriptEnabled) {
          await aftertaste.locator("#chapter-query").fill("不存在的峰终XYZ");
          await aftertaste.locator(`#${id} a[href='#${anchor}']`).first().click();
          await aftertaste.waitForFunction(() => document.getElementById("c10").open &&
            !document.getElementById("c10").hidden && document.getElementById("chapter-query").value === "");
          assert.equal(new URL(aftertaste.url()).hash, "#" + anchor);
        }
      }
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    // Senses: distinguish reported price, enjoyment, and what a blind test excludes.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const senses = await context.newPage();
      const failures = [], network = [];
      senses.on("pageerror", error => failures.push(error.message));
      senses.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await senses.goto(url + (javaScriptEnabled ? "#c02" : ""));
      if (!javaScriptEnabled) await senses.locator("#c02 > summary").click();
      assert.match(await senses.locator("#c02 .prose").textContent(), /身体还是生活发生的地方/);
      for (const anchor of ["senses-thermal-touch", "senses-three-layers", "senses-price-expectation", "senses-blind-test"]) {
        if (javaScriptEnabled) {
          await senses.locator(`#c02 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(senses.url()).hash, "#" + anchor);
        }
        await senses.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      assert.equal(await senses.locator("#c02 .prose table").count(), 3);
      for (const table of await senses.locator("#c02 .prose table").all()) {
        assert((await table.boundingBox()).width <= 350);
      }
      if (javaScriptEnabled) {
        await senses.locator("#c02 a[href='#n19']").first().click();
        await senses.waitForFunction(() => document.getElementById("n19").open);
      } else {
        await senses.locator("#n19 > summary").click();
      }
      for (const selector of ["#c02 .prose", "#n19 .prose"]) {
        const shape = await senses.locator(selector).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, selector);
      }
      assert.match(await senses.locator("#n19 .prose").textContent(), /告知价格/);
      if (javaScriptEnabled) {
        await senses.locator("#n19 a[href='#senses-price-expectation']").last().click();
        assert.equal(new URL(senses.url()).hash, "#senses-price-expectation");
        assert(await senses.locator("#c02 .prose").isVisible());
      }
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    // Spending: future costs and use remain distinct from original payments.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const spending = await context.newPage();
      const failures = [], network = [];
      spending.on("pageerror", error => failures.push(error.message));
      spending.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await spending.goto(url + (javaScriptEnabled ? "#c06" : ""));
      if (!javaScriptEnabled) await spending.locator("#c06 > summary").click();
      assert.match(await spending.locator("#c06 .prose").textContent(), /钱买来的应该是你想过的生活/);
      for (const anchor of ["spending-matching-life", "spending-pass-arithmetic", "spending-learning", "spending-theatre-study", "spending-future-cost"]) {
        if (javaScriptEnabled) {
          await spending.locator(`#c06 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(spending.url()).hash, "#" + anchor);
        }
        await spending.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      assert.equal(await spending.locator("#c06 .prose table").count(), 4);
      for (const table of await spending.locator("#c06 .prose table").all()) {
        assert((await table.boundingBox()).width <= 350);
      }
      if (javaScriptEnabled) {
        await spending.locator("#c06 a[href='#n20']").first().click();
        await spending.waitForFunction(() => document.getElementById("n20").open);
      } else {
        await spending.locator("#n20 > summary").click();
      }
      for (const selector of ["#c06 .prose", "#n20 .prose"]) {
        const shape = await spending.locator(selector).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, selector);
      }
      assert.match(await spending.locator("#n20 .prose").textContent(), /单尾p < .05/);
      const doi = spending.locator("#n20 a[href='https://doi.org/10.1016/0749-5978%2885%2990049-4']");
      assert.equal(await doi.count(), 1);
      if (javaScriptEnabled) {
        await spending.locator("#n20 a[href='#spending-theatre-study']").last().click();
        assert.equal(new URL(spending.url()).hash, "#spending-theatre-study");
        assert(await spending.locator("#c06 .prose").isVisible());
      }
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    // Cognitive labor: the project summary is not promoted to a full-paper record.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const constrained = await context.newPage();
      const failures = [], network = [];
      constrained.on("pageerror", error => failures.push(error.message));
      constrained.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await constrained.goto(url + (javaScriptEnabled ? "#c09" : ""));
      if (!javaScriptEnabled) await constrained.locator("#c09 > summary").click();
      assert.match(await constrained.locator("#c09 .prose").textContent(), /三种安排没有实验排名/);
      for (const anchor of ["constrained-cognitive", "constrained-three-arrangements", "constrained-authority"]) {
        if (javaScriptEnabled) {
          await constrained.locator(`#c09 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(constrained.url()).hash, "#" + anchor);
        }
        await constrained.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      assert.equal(await constrained.locator("#c09 .prose table").count(), 3);
      for (const table of await constrained.locator("#c09 .prose table").all()) {
        assert((await table.boundingBox()).width <= 350);
      }
      if (javaScriptEnabled) {
        await constrained.locator("#c09 a[href='#f50']").first().click();
        await constrained.waitForFunction(() => document.getElementById("f50").open);
      } else {
        await constrained.locator("#f50 > summary").click();
      }
      for (const selector of ["#c09 .prose", "#f50 .prose"]) {
        const shape = await constrained.locator(selector).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, selector);
      }
      assert.match(await constrained.locator("#f50 .prose").textContent(), /不能直接充当2019年论文的样本量/);
      if (javaScriptEnabled) {
        await constrained.locator("#f50 a[href='#constrained-cognitive']").last().click();
        assert.equal(new URL(constrained.url()).hash, "#constrained-cognitive");
        assert(await constrained.locator("#c09 .prose").isVisible());
      }
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    // Dance: static time relations, original arithmetic, and scoped work records.
    for (const javaScriptEnabled of [true, false]) {
      const context = await browser.newContext({viewport: {width: 390, height: 844}, javaScriptEnabled, reducedMotion: "reduce"});
      const dance = await context.newPage();
      const failures = [], network = [];
      dance.on("pageerror", error => failures.push(error.message));
      dance.on("request", request => {if (/^https?:/.test(request.url())) network.push(request.url());});
      await dance.goto(url + (javaScriptEnabled ? "#c27" : ""));
      if (!javaScriptEnabled) await dance.locator("#c27 > summary").click();
      for (const anchor of ["dance-time-grid", "dance-rosas", "dance-chance"]) {
        if (javaScriptEnabled) {
          await dance.locator(`#c27 a[href='#${anchor}']`).first().click();
          assert.equal(new URL(dance.url()).hash, "#" + anchor);
        }
        await dance.locator("#" + anchor).scrollIntoViewIfNeeded();
      }
      const image = dance.locator("#c27 .prose img");
      await image.scrollIntoViewIfNeeded();
      await decodeImage(image);
      assert.equal(await image.count(), 1);
      assert.match(await image.getAttribute("alt"), /第3格甲为R、乙为Q、丙为P/);
      const imageShape = await image.evaluate(el => ({
        natural: [el.naturalWidth, el.naturalHeight], width: el.getBoundingClientRect().width
      }));
      assert.deepEqual(imageShape.natural, [720, 1080]);
      assert(imageShape.width <= 350);
      assert.match(await dance.locator("#c27 .prose").textContent(), /三分之二/);
      assert.equal(await dance.locator("#c27 .prose table").count(), 2);
      for (const [id, anchor, phrase] of [
        ["f51", "dance-rosas", /未观看并核验完整演出/],
        ["f52", "dance-chance", /不是Cunningham使用过的算法/]
      ]) {
        if (javaScriptEnabled) {
          await dance.locator(`#c27 a[href='#${id}']`).first().click();
          await dance.waitForFunction(id => document.getElementById(id).open, id);
        } else {
          await dance.locator(`#${id} > summary`).click();
        }
        assert.match(await dance.locator(`#${id} .prose`).textContent(), phrase);
        const shape = await dance.locator(`#${id} .prose`).evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
        assert(shape.scroll <= shape.client + 1, id);
        if (javaScriptEnabled) {
          await dance.locator(`#${id} a[href='#${anchor}']`).last().click();
          assert.equal(new URL(dance.url()).hash, "#" + anchor);
          assert(await dance.locator("#c27 .prose").isVisible());
        }
      }
      const shape = await dance.locator("#c27 .prose").evaluate(el => ({client: el.clientWidth, scroll: el.scrollWidth}));
      assert(shape.scroll <= shape.client + 1);
      assert.deepEqual(failures, []);
      assert.deepEqual(network, []);
      await context.close();
    }
    console.log("OK: offline, filters, empty state, deep links, keyboard, 390px, dark/reduced motion, print, no-JS, zero external requests");
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
