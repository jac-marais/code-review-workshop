import { loadCustomerSummary } from "./data";
import type { CustomerSummary } from "./types";

const summaryCache = new Map<string, CustomerSummary>();

export async function getCustomerSummary(
  tenantId: string,
  customerId: string,
): Promise<CustomerSummary | undefined> {
  const cached = summaryCache.get(customerId);
  if (cached) {
    return cached;
  }

  const summary = await loadCustomerSummary(tenantId, customerId);
  if (summary) {
    summaryCache.set(customerId, summary);
  }
  return summary;
}

export function resetSummaryCache(): void {
  summaryCache.clear();
}
