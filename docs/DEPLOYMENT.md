# Deployment

Voyager Link is deployed in production on Cloudflare Workers at `https://voyager-1-live-receiver.simondalmasso44.workers.dev`. Production is promoted only from an audited exact branch SHA after full regression, CodeQL/security checks, retained Wrangler dry-run evidence and post-deploy black-box verification. Material verification failure triggers rollback to the previously accepted Cloudflare version.

The current Order 011 work remains isolated on draft PR #12 (`feat/order-011-deep-space-lab`); `main` is intentionally not merged and remains the repository baseline until a separate AUD decision authorizes otherwise. `wrangler.jsonc` defines Worker `voyager-1-live-receiver`, static assets, SPA fallback, ASSETS binding and `/api/*` worker-first routing.

Build locally with `npm run build`; validate packaging with `npx wrangler@4.114.0 deploy --dry-run --outdir .wrangler-dry-run`. Remote deploy is authorized only through the explicit terminal AUD gate for the active order. Cost guard remains `USD_BUDGET=0`, payment data is forbidden, and no RF uplink, telescope-control or DSN-control capability is deployed.
