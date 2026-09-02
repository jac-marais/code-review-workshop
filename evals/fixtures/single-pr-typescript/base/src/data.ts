import type { CustomerSummary } from "./types";

const customers = new Map<string, CustomerSummary>([
  [
    "tenant-a:shared",
    {
      tenantId: "tenant-a",
      customerId: "shared",
      name: "Alice <img src=x onerror=alert(1)>",
      balance: 1250,
    },
  ],
  [
    "tenant-b:shared",
    {
      tenantId: "tenant-b",
      customerId: "shared",
      name: "Bob",
      balance: 875,
    },
  ],
  [
    "tenant-a:zero",
    {
      tenantId: "tenant-a",
      customerId: "zero",
      name: "Zero Balance",
      balance: 0,
    },
  ],
]);

export async function loadCustomerSummary(
  tenantId: string,
  customerId: string,
): Promise<CustomerSummary | undefined> {
  return customers.get(`${tenantId}:${customerId}`);
}
