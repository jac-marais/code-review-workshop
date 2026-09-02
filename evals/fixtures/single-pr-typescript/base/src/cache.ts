import { loadCustomerSummary } from "./data";
import type { CustomerSummary } from "./types";

export async function getCustomerSummary(
  tenantId: string,
  customerId: string,
): Promise<CustomerSummary | undefined> {
  return loadCustomerSummary(tenantId, customerId);
}

export function resetSummaryCache(): void {
  // The base implementation has no shared cache.
}
