import json
import tempfile
import unittest
from pathlib import Path

from media_workbench.ocr import run_tesseract_ocr


class OcrEngineTests(unittest.TestCase):
    def test_tesseract_adapter_writes_searchable_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "sample.png"
            source.write_bytes(b"image placeholder")

            fake_tesseract = root / "tesseract"
            fake_tesseract.write_text("#!/usr/bin/env bash\nprintf 'Invoice total 42\\n'\n", encoding="utf-8")
            fake_tesseract.chmod(0o755)

            out = run_tesseract_ocr(root, "asset-ocr", source, command=str(fake_tesseract))

            self.assertEqual((out / "text.txt").read_text(encoding="utf-8"), "Invoice total 42\n")
            payload = json.loads((out / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["engine"], "tesseract-cli")
            self.assertEqual(payload["source_path"], str(source))
            self.assertEqual(payload["blocks"][0]["text"], "Invoice total 42")


if __name__ == "__main__":
    unittest.main()
