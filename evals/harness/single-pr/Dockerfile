FROM mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48

USER root
WORKDIR /fixture-manifest
COPY evals/fixtures/single-pr-typescript/base/package.json \
     evals/fixtures/single-pr-typescript/base/package-lock.json ./
RUN mkdir -p /opt/npm-cache \
    && npm ci --ignore-scripts --cache /opt/npm-cache \
    && chmod -R a+rX /opt/npm-cache /fixture-manifest

COPY evals/harness/single-pr/entrypoint.sh \
     evals/harness/single-pr/browser_check.cjs \
     evals/harness/single-pr/reproduce_tenant_cache.cjs \
     evals/harness/single-pr/sandbox_canary.sh /harness/
RUN chmod 0555 /harness/entrypoint.sh /harness/sandbox_canary.sh \
    && chmod 0444 /harness/browser_check.cjs /harness/reproduce_tenant_cache.cjs

WORKDIR /workspace
ENTRYPOINT ["/harness/entrypoint.sh"]
