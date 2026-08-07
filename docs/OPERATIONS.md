# Operations

Start the web runtime with `npm run dev`; health is `/api/v1/health`. Start a synthetic listener with `PYTHONPATH=listener-agent/src python -m voyager_listener.cli serve --synthetic`. Use `/health`, `/snapshot`, and `/events` for listener diagnostics. Update source snapshots only through reviewed commits. If an upstream fails, preserve the scene and display `STALE` or `UNAVAILABLE`. Local rollback is `git checkout <known-sha>` followed by a clean build. No remote operation is part of this checkpoint.
