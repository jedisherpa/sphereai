# Wave 1 Research: Packaging and Install

## Platform strategy
- Windows: Tauri MSI/NSIS installers
- macOS: signed app bundle + notarization workflow
- Linux: AppImage first, optional distro packages later

## Model delivery strategy options
1. Bundle large models in installer (poor size UX)
2. First-run downloader with cache verification (recommended)
3. Separate offline model bundle package (recommended companion option)

## Recommendation
Use **slim installer + first-run model manager** with optional offline bundle for air-gapped use.

## Sources
- https://v2.tauri.app/distribute/windows-installer/
- https://www.pyinstaller.org/en/stable/usage.html
