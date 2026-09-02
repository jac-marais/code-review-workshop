# Customer Summary Service

Run `npm ci`, `npm test`, and `npm start`.

The summary route accepts `tenant` and `customer` query parameters:

```text
/summary?tenant=tenant-a&customer=shared
```

Tenant identity comes from the authenticated request in production. This fixture passes it as a query parameter so the route can be exercised locally.
