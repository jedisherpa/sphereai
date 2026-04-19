import json
import tempfile
import unittest
from pathlib import Path

from media_workbench.asr import run_whisper_asr


class AsrEngineTests(unittest.TestCase):
    def test_whisper_adapter_writes_canonical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "sample.wav"
            source.write_bytes(b"RIFF audio placeholder")

            fake_whisper = root / "whisper"
            fake_whisper.write_text(
                """#!/usr/bin/env bash
set -euo pipefail
input="$1"
out_dir=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--output_dir" ]; then
    out_dir="$2"
    break
  fi
  shift
done
stem="$(basename "$input")"
stem="${stem%.*}"
mkdir -p "$out_dir"
printf 'Hello local transcription\\n' > "$out_dir/$stem.txt"
printf '1\\n00:00:00,000 --> 00:00:01,000\\nHello local transcription\\n' > "$out_dir/$stem.srt"
printf '{"text":"Hello local transcription"}\\n' > "$out_dir/$stem.json"
""",
                encoding="utf-8",
            )
            fake_whisper.chmod(0o755)

            out = run_whisper_asr(root, "asset-asr", source, command=str(fake_whisper))

            self.assertEqual((out / "transcript.txt").read_text(encoding="utf-8"), "Hello local transcription\n")
            self.assertTrue((out / "transcript.srt").read_text(encoding="utf-8").startswith("1\n"))
            payload = json.loads((out / "transcript.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["text"], "Hello local transcription")


if __name__ == "__main__":
    unittest.main()
