# Deployment

Current state is pre-deploy only. `wrangler.jsonc` defines Worker `voyager-1-live-receiver`, compatibility date 2026-08-05, static assets, SPA fallback, ASSETS binding, and `/api/*` worker-first. Build with `npm run build`; validate with `npx wrangler@4.114.0 deploy --dry-run --outdir .wrangler-dry-run`. The exact future remote command is `npx wrangler@4.114.0 deploy`, which is explicitly not authorized in AUD-001. No remote resource is required in V1.
