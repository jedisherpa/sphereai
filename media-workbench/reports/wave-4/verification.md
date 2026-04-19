# Wave 4 Verification

## Commands run
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `printf 'sample audio bytes' > /tmp/sample.wav && PYTHONPATH=src python -m media_workbench.main wave2 --workspace ./workspace --sample /tmp/sample.wav`
- `python -m compileall src`

## Evidence
- Recovery test verifies `running -> retrying` transition at startup.
- Engine test verifies processing metrics are persisted.
- Status endpoint returns queue counts and settings.
