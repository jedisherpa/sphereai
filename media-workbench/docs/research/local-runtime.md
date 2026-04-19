# Wave 1 Research: Local Runtime and App Shell

## Options considered
1. Browser-only local web app + local backend
2. Tauri shell + local backend
3. Electron shell + local backend

## Evaluation
- **Browser-only**: simplest dev loop but weaker native integration/distribution UX.
- **Tauri**: smaller bundles and strong desktop packaging path, Rust sidecar patterns useful for local services.
- **Electron**: mature ecosystem and process model, but generally larger distribution footprint.

## Recommendation
Choose **Tauri + local backend** for main installable app, with optional helper process for advanced OS integration.

## Sources
- https://v2.tauri.app/
- https://v2.tauri.app/distribute/windows-installer/
- https://www.electronjs.org/docs/latest/tutorial/process-model
