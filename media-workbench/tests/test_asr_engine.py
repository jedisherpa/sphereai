import json
import os
import tempfile
import unittest
import wave
from pathlib import Path

from media_workbench.asr import run_whisper_asr, run_xenova_asr


class AsrEngineTests(unittest.TestCase):
    def test_whisper_adapter_writes_canonical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "sample.wav"
            with wave.open(str(source), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(b"\x00\x00" * 16000)

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

    def test_xenova_adapter_invokes_runner_with_model_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "sample.wav"
            with wave.open(str(source), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(b"\x00\x00" * 16000)
            model_root = root / "models"
            (model_root / "Xenova" / "whisper-small").mkdir(parents=True)

            fake_runner = root / "xenova_runner.mjs"
            fake_runner.write_text(
                """import fs from 'fs';
import path from 'path';
const [, , audioPath, outDir, assetHash] = process.argv;
if (!process.env.MEDIA_WORKBENCH_XENOVA_MODEL_ROOT) process.exit(2);
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'transcript.txt'), `Xenova transcript for ${assetHash}\\n`);
fs.writeFileSync(path.join(outDir, 'transcript.srt'), '1\\n00:00:00,000 --> 00:00:01,000\\nXenova transcript\\n');
fs.writeFileSync(path.join(outDir, 'transcript.json'), JSON.stringify({ audioPath, assetHash, engine: 'xenova-transformers' }));
""",
                encoding="utf-8",
            )

            old_root = os.environ.get("MEDIA_WORKBENCH_XENOVA_MODEL_ROOT")
            os.environ["MEDIA_WORKBENCH_XENOVA_MODEL_ROOT"] = str(model_root)
            try:
                out = run_xenova_asr(root, "asset-xenova", source, runner=fake_runner)
            finally:
                if old_root is None:
                    os.environ.pop("MEDIA_WORKBENCH_XENOVA_MODEL_ROOT", None)
                else:
                    os.environ["MEDIA_WORKBENCH_XENOVA_MODEL_ROOT"] = old_root

            self.assertEqual((out / "transcript.txt").read_text(encoding="utf-8"), "Xenova transcript for asset-xenova\n")
            payload = json.loads((out / "transcript.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["engine"], "xenova-transformers")


if __name__ == "__main__":
    unittest.main()
