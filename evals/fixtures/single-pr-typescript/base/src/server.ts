import { createServer as createHttpServer, type Server } from "node:http";
import { URL } from "node:url";

import { getCustomerSummary } from "./cache";
import { escapeHtml } from "./html";

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

export function createServer(): Server {
  return createHttpServer(async (request, response) => {
    const url = new URL(request.url ?? "/", "http://fixture.test");
    if (url.pathname !== "/summary") {
      response.writeHead(404).end("Not found");
      return;
    }

    const tenantId = url.searchParams.get("tenant") ?? "";
    const customerId = url.searchParams.get("customer") ?? "";
    const summary = await getCustomerSummary(tenantId, customerId);
    if (!summary) {
      response.writeHead(404).end("Customer not found");
      return;
    }

    const renderedBalance = formatCurrency(summary.balance);
    const html = `<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Customer summary</title></head>
  <body>
    <main>
      <h1>Customer ${escapeHtml(summary.customerId)}</h1>
      <p data-testid="balance">${renderedBalance}</p>
    </main>
  </body>
</html>`;
    response.writeHead(200, { "content-type": "text/html; charset=utf-8" }).end(html);
  });
}

if (require.main === module) {
  const port = Number(process.env.PORT ?? 3000);
  createServer().listen(port, "127.0.0.1", () => {
    console.log(`customer summary listening on ${port}`);
  });
}
