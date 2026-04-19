# Wave 1 Research: ASR Stack

## Options considered
1. OpenAI Whisper reference implementation
2. faster-whisper (CTranslate2)
3. whisper.cpp

## Evaluation
- **OpenAI Whisper ref**: canonical baseline and model card, but heavier runtime footprint.
- **faster-whisper**: optimized inference using CTranslate2, generally better local throughput/memory tradeoff.
- **whisper.cpp**: compelling CPU/offline deployment characteristics and C/C++ portability.

## Recommendation
- Baseline policy: **Whisper large model family** for quality target.
- Runtime default for v1: **faster-whisper** with configurable model profile (`large-v3`, fallbacks for weaker hardware).
- Keep **whisper.cpp** as contingency path for constrained devices.

## Risks
- Large model viability on 16GB systems and CPU-only machines.

## Sources
- https://github.com/openai/whisper
- https://github.com/openai/whisper/blob/main/model-card.md
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/ggml-org/whisper.cpp
