# Install Guide

## Current packaging state
Wave 5 remains source-run oriented.

## Local run
1. Ensure Python 3.10+ is available.
2. `cd media-workbench`
3. `PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765`

## Optional local OCR
Install Tesseract to enable real local OCR for image jobs. If Tesseract is not installed, image OCR jobs fall back to the deterministic spike output so API testing still works.

- macOS Homebrew: `brew install tesseract`
- Override path when needed: `MEDIA_WORKBENCH_TESSERACT=/path/to/tesseract`

## Optional local ASR
Install a local Whisper-compatible CLI named `whisper` to enable real local transcription for audio jobs. If it is not installed, ASR jobs fall back to the deterministic spike output so API testing still works.

- macOS Homebrew: `brew install openai-whisper`
- Override path when needed: `MEDIA_WORKBENCH_WHISPER=/path/to/whisper`

## Planned installers
- Windows MSI/NSIS (planned)
- macOS app bundle + notarization (planned)
- Linux AppImage (planned)
