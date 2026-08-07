# Dependency and GitHub Actions policy

Runtime JavaScript dependencies are empty. Tooling dependencies are exact versions in `package.json` and `package-lock.json`. CI runs `npm audit --omit=dev --audit-level=moderate` as a blocking runtime gate and records a complete tooling audit separately. Every tooling advisory must appear in `artifacts/dependency-audit-triage.json` with package, severity, advisory URL, dependency path and shipping assessment; unclassified entries fail CI.

Official GitHub Actions are referenced by maintained major tags (`actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`, `github/codeql-action/*@v3`). The policy is: official publisher only, least permissions, Dependabot review, no third-party action without immutable SHA review. This documented major-tag policy is chosen because the repository owner maintains updates through GitHub's first-party release channels.

Secret scanning covers the working tree and full Git history for cloud tokens, GitHub tokens and private service credentials. The Ed25519 private key under `tests/fixtures` is a deliberately public test fixture and is cryptographically barred from production.

The HEAD commit may be unsigned. Audit output must state that fact and must not imply a Git signature.
