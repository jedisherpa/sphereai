# Wave 2 Verification

## Commands run
- `PYTHONPATH=src python -m media_workbench.main`
- `PYTHONPATH=src python -m media_workbench.main wave2 --workspace ./workspace --sample /tmp/sample.wav`
- `python -m compileall src`
- `PYTHONPATH=src python -m unittest discover -s tests -v`

## Evidence
- Workspace directory tree created with expected structure.
- `app.db` created with required tables.
- Derived OCR/transcript/clip outputs written under deterministic paths.
- Queue job progressed to completed state.
