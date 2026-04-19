# Wave 1 Research: Diarization and Speaker Clips

## Options considered
1. pyannote.audio community pipeline
2. Basic VAD segmentation only (no diarization)
3. Commercial diarization APIs (rejected for core)

## Evaluation
- **pyannote.audio**: strongest open ecosystem for speaker diarization workflows; local execution possible.
- **VAD-only**: simpler but does not satisfy recurring speaker clustering requirements.
- **Cloud APIs**: conflicts with local-first default for core workflows.

## Recommendation
Use **pyannote.audio** as optional local diarization module with explicit note that quality varies and manual review is required.

## Clip pipeline notes
- Extract per-speaker segments with ffmpeg.
- Persist deterministic clip naming by asset-id + segment span + cluster id.

## Sources
- https://github.com/pyannote/pyannote-audio
- https://huggingface.co/pyannote/speaker-diarization-community-1
- https://ffmpeg.org/legal.html
