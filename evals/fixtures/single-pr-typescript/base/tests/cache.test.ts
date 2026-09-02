import assert from "node:assert/strict";
import test from "node:test";

import { getCustomerSummary, resetSummaryCache } from "../src/cache";

test("returns a customer summary", async () => {
  resetSummaryCache();
  const summary = await getCustomerSummary("tenant-a", "shared");
  assert.equal(summary?.name.startsWith("Alice"), true);
});
