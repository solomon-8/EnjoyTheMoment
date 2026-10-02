// Optional EPUB rendering regression, separate from EPUBCheck and browser.cjs.
// Development-only modules: playwright, epubjs and jszip (install outside repo).
// NODE_PATH must resolve those modules. CHROME_BIN optionally selects Chromium.
// node tests/epub_browser.cjs [--epub FILE] [--report FILE] [--screenshots DIR]
// Checks first/last non-whitespace character of every nonempty table cell at
// 320px/125%, 390px/100%, and 800px/100%. It does not prove every interior glyph,
// cross-reader compatibility, accessibility or reader comprehension.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const JSZip = require("jszip");
const {chromium} = require("playwright");

const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  assert(["--epub", "--report", "--screenshots"].includes(process.argv[i]),
    "Unknown option: " + process.argv[i]);
  assert(process.argv[i + 1], "Missing option value");
  options[process.argv[i]] = path.resolve(process.argv[i + 1]);
}
const archivePath = options["--epub"] || path.resolve(__dirname, "../downloads/EnjoyTheMoment.epub");
const archiveBytes = fs.readFileSync(archivePath);
const moduleFiles = {
  "/epub.js": require.resolve("epubjs/dist/epub.min.js"),
  "/jszip.js": require.resolve("jszip/dist/jszip.min.js"),
};
const documentHtml = `<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0;width:100%;height:100%}#reader{width:100%;height:100vh}</style>
</head><body><div id="reader"></div><script src="/jszip.js"></script>
<script src="/epub.js"></script><script>
window.book=ePub('/book.epub');window.ready=book.ready.then(async()=>{
window.rendition=book.renderTo('reader',{width:'100%',height:'100%',spread:'none',flow:'paginated'});
await rendition.display();});</script></body></html>`;
const server = http.createServer((req, res) => {
  const pathname = req.url.split("?")[0];
  if (pathname === "/") {
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.end(documentHtml);
  } else if (pathname === "/book.epub") {
    res.setHeader("Content-Type", "application/epub+zip");
    res.end(archiveBytes);
  } else if (moduleFiles[pathname]) {
    res.setHeader("Content-Type", "text/javascript");
    res.end(fs.readFileSync(moduleFiles[pathname]));
  } else {
    res.writeHead(404); res.end();
  }
});

(async () => {
  const zip = await JSZip.loadAsync(archiveBytes);
  // Enumerate actual generated XHTML rather than maintaining a chapter whitelist.
  const cases = [];
  for (const name of Object.keys(zip.files).sort()) {
    if (!/^EPUB\/text\/.+\.xhtml$/.test(name)) continue;
    const text = await zip.file(name).async("string");
    const count = (text.match(/<table(?:\s|>)/g) || []).length;
    for (let index = 0; index < count; index++) {
      cases.push({file: name.slice("EPUB/".length), table: index});
    }
  }
  assert(cases.length > 0, "No tables found: cannot pass an empty inventory");
  if (options["--screenshots"]) fs.mkdirSync(options["--screenshots"], {recursive:true});
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const url = `http://127.0.0.1:${server.address().port}/`;
  let browser;
  const report = {
    archive_sha256: crypto.createHash("sha256").update(archiveBytes).digest("hex"),
    tables: cases.length, rows: [], errors: [], external_requests: [],
    scope: "nonempty table-cell first/last character visibility in epub.js/Chromium",
  };
  try {
    browser = await chromium.launch({
      headless:true,
      ...(process.env.CHROME_BIN ? {executablePath:process.env.CHROME_BIN} : {}),
    });
    for (const [width, large] of [[320,true], [390,false], [800,false]]) {
      const context = await browser.newContext({viewport:{width, height:950}});
      const page = await context.newPage();
      page.on("pageerror", error => report.errors.push({width, message:error.message}));
      page.on("request", request => {
        if (/^https?:/.test(request.url()) && !request.url().startsWith(url)) {
          report.external_requests.push(request.url());
        }
      });
      await page.goto(url);
      await page.evaluate(() => window.ready);
      if (large) await page.evaluate(() => rendition.themes.fontSize("125%"));
      for (const item of cases) {
        await page.evaluate(file => rendition.display(file), item.file);
        const result = await page.evaluate(async ({index, width}) => {
          const contents = rendition.getContents()[0];
          const table = contents.document.querySelectorAll("table")[index];
          if (!table) throw new Error("Table missing in rendered document");
          const targets = [];
          for (const [cellIndex, cell] of [...table.querySelectorAll("th,td")].entries()) {
            const walker = contents.document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
            const texts = [];
            let node;
            while ((node = walker.nextNode())) {
              if (node.textContent.trim()) texts.push(node);
            }
            if (!texts.length) continue;
            for (const end of [false, true]) {
              const text = end ? texts.at(-1) : texts[0];
              let start = end ? text.textContent.trimEnd().length - 1 :
                text.textContent.search(/\S/);
              if (end && /[\uDC00-\uDFFF]/.test(text.textContent[start])) start--;
              const length = text.textContent.codePointAt(start) > 0xFFFF ? 2 : 1;
              const range = contents.document.createRange();
              range.setStart(text, start); range.setEnd(text, start + length);
              targets.push({cell:cellIndex, end, node:text, start, length,
                cfi:contents.cfiFromRange(range)});
            }
          }
          const failures = [];
          for (const target of targets) {
            await rendition.display(target.cfi);
            const range = contents.document.createRange();
            range.setStart(target.node, target.start);
            range.setEnd(target.node, target.start + target.length);
            const rect = range.getBoundingClientRect();
            const frame = document.querySelector("#reader iframe").getBoundingClientRect();
            const screen = {x:rect.x + frame.x, y:rect.y + frame.y,
              width:rect.width, height:rect.height};
            if (!(screen.width > 0 && screen.x >= -1 &&
                screen.x + screen.width <= width + 1 && screen.y >= -1 &&
                screen.y + screen.height <= 951)) {
              failures.push({cell:target.cell, end:target.end,
                text:target.node.textContent.slice(0, 100), screen});
            }
          }
          return {cells:targets.length / 2, checks:targets.length, failures};
        }, {index:item.table, width});
        report.rows.push({...item, width, large, ...result});
        if (options["--screenshots"] &&
            (result.failures.length || (item.table === 0 &&
             ["text/guides--README.xhtml", "text/assets--art--README.xhtml"].includes(item.file)))) {
          const filename = `${item.file.replaceAll("/", "-")}-${item.table}-${width}.png`;
          await page.screenshot({path:path.join(options["--screenshots"], filename)});
        }
      }
      await context.close();
      const rows = report.rows.filter(row => row.width === width);
      console.log(`${width}px/${large ? 125 : 100}%: ${rows.length} tables, ` +
        `${rows.reduce((n,row) => n + row.checks, 0)} cell endpoints, ` +
        `${rows.reduce((n,row) => n + row.failures.length, 0)} failures`);
    }
    assert.equal(report.rows.length, cases.length * 3);
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.external_requests, []);
    const failed = report.rows.filter(row => row.failures.length);
    assert.deepEqual(failed, [], "Some table-cell endpoints cannot be read");
    console.log("OK: table-cell endpoint navigation; no claim about comprehension or all reading systems");
  } finally {
    if (options["--report"]) {
      fs.writeFileSync(options["--report"], JSON.stringify(report, null, 2) + "\n");
    }
    if (browser) await browser.close();
    server.close();
  }
})().catch(error => {
  console.error(error);
  server.close();
  process.exitCode = 1;
});
