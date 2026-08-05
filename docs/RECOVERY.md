# Recovery

From a clean checkout, use Node 24.18.0, npm 11, Python 3.12+, `npm ci`, all tests, build, data verification, listener tests, and Wrangler dry-run. Data files have SHA-256 output through `npm run verify:data`; signal fixtures are regenerated with seed 1701. A future failed Worker deploy should roll back to the previously verified Worker version independently of GitHub. GitHub branch/PR changes and Cloudflare rollback are separate authority domains.
