# Wave 5 Verification

## Commands run
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `printf 'sample audio bytes' > /tmp/sample.wav && PYTHONPATH=src python -m media_workbench.main wave2 --workspace ./workspace --sample /tmp/sample.wav`
- `python -m compileall src`

## Evidence
- New quality tests passed for cancel/retry flow, search/export, and invalid API ingest behavior.
- Existing wave tests continue to pass.
