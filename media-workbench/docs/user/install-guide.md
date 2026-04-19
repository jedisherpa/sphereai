# Install Guide

## Current packaging state
Wave 5 remains source-run oriented.

## Local run
1. Ensure Python 3.10+ is available.
2. `cd media-workbench`
3. `PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765`

## Planned installers
- Windows MSI/NSIS (planned)
- macOS app bundle + notarization (planned)
- Linux AppImage (planned)
