# Wave 1 Research: OCR Stack

## Options considered
1. PaddleOCR + OpenCV preprocessing (Python worker)
2. Tesseract + OpenCV preprocessing
3. Cloud OCR APIs (rejected for core)

## Evaluation
- **PaddleOCR**: strong multilingual support and practical OCR toolkit orientation; Apache-2.0 friendly baseline.
- **Tesseract**: mature and lightweight, but box/confidence behavior and modern scene-text quality are often weaker for mixed screenshot artifacts.
- **Cloud OCR**: violates local-first default for core flow.

## Recommendation
Choose **PaddleOCR + OpenCV** executed in isolated local worker processes.

## Packaging implications
- Bundle runtime deps where feasible.
- Prefer model-on-first-run download/cache to avoid oversized installer.

## Sources
- https://github.com/PaddlePaddle/PaddleOCR
- https://opencv.org/license/
- https://github.com/tesseract-ocr/tesseract
