# Security

The Worker has fixed upstream URLs, timeouts, size limits, typed parameter ranges, safe error bodies, no stack traces, and security headers. DSN XML with DTD/entities is rejected. The browser CSP allows same-origin plus the loopback listener. The listener binds to loopback, requires explicit remote opt-in, supports an environment bearer token, limits endpoints, does not execute browser commands, and exposes no hardware mutation. No secrets, analytics, payments, arbitrary proxy URL, or remote storage are required.
