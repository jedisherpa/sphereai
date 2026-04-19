# Wave 1 Licensing Audit (Initial)

## Candidate dependencies and license posture
- PaddleOCR: Apache-2.0 (verify exact model artifact terms per selected model)
- OpenCV: Apache-2.0 (4.5+)
- Whisper codebase: MIT
- faster-whisper: MIT
- pyannote.audio: MIT, but model access terms may apply on Hugging Face
- FFmpeg: LGPL 2.1+ baseline; GPL features can change redistribution obligations
- SQLite: Public domain / permissive distribution norms

## Actions before lock
1. Freeze exact package versions.
2. Verify transitive dependency licenses for runtime bundles.
3. Separate OSS code license from model-weight redistribution terms.
4. Produce THIRD_PARTY_NOTICES template.

## Sources
- https://github.com/openai/whisper
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/pyannote/pyannote-audio
- https://ffmpeg.org/legal.html
- https://opencv.org/license/
