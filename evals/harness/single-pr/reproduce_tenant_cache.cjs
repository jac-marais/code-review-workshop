const { getCustomerSummary, resetSummaryCache } = require("/workspace/dist/src/cache");

async function main() {
  resetSummaryCache();
  const tenantA = await getCustomerSummary("tenant-a", "shared");
  const tenantB = await getCustomerSummary("tenant-b", "shared");
  const evidence = {
    firstTenant: tenantA?.tenantId,
    requestedSecondTenant: "tenant-b",
    returnedSecondTenant: tenantB?.tenantId,
    returnedSecondName: tenantB?.name,
  };
  process.stdout.write(`${JSON.stringify(evidence)}\n`);
  if (tenantA?.tenantId !== "tenant-a" || tenantB?.tenantId !== "tenant-a") {
    throw new Error("the cross-tenant cache reproduction did not occur");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
