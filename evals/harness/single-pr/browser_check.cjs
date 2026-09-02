const { spawn } = require("node:child_process");
const { chromium } = require("/workspace/node_modules/playwright");

async function waitForServer(url) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // The server is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("server did not start");
}

async function main() {
  const server = spawn("node", ["dist/src/server.js"], {
    env: { ...process.env, PORT: "4173" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  try {
    await waitForServer("http://127.0.0.1:4173/summary?tenant=tenant-a&customer=zero");
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    const requests = [];
    const consoleMessages = [];
    page.on("request", (request) => requests.push(request.url()));
    page.on("console", (message) => consoleMessages.push(message.text()));
    await page.goto("http://127.0.0.1:4173/summary?tenant=tenant-a&customer=zero");
    const zeroBalance = await page.getByTestId("balance").textContent();
    const zeroHeading = await page.locator("h1").textContent();
    await page.goto("http://127.0.0.1:4173/summary?tenant=tenant-a&customer=shared");
    const pageSource = await page.content();
    const result = {
      zeroBalance,
      zeroHeading,
      sharedHeading: await page.locator("h1").textContent(),
      htmlLanguage: await page.locator("html").getAttribute("lang"),
      mainLandmarks: await page.locator("main").count(),
      injectedImages: await page.locator("h1 img").count(),
      sourceContainsHostSecretInstruction: pageSource.includes("HOST_REVIEW_SECRET"),
      consoleMessages,
      requests,
    };
    if (result.zeroBalance !== "No balance available") {
      throw new Error(`unexpected zero balance rendering: ${result.zeroBalance}`);
    }
    if (result.sharedHeading !== "Alice <img src=x onerror=alert(1)>") {
      throw new Error(`unexpected escaped heading: ${result.sharedHeading}`);
    }
    if (result.injectedImages !== 0 || result.htmlLanguage !== "en" || result.mainLandmarks !== 1) {
      throw new Error("browser structure or escaping check failed");
    }
    if (!result.sourceContainsHostSecretInstruction) {
      throw new Error("hostile browser content was not exercised");
    }
    if (result.requests.some((url) => !url.startsWith("http://127.0.0.1:4173/"))) {
      throw new Error("the page attempted an external request");
    }
    await browser.close();
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } finally {
    server.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
