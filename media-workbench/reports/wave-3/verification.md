# Wave 3 Verification

## Commands run
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `printf 'sample audio bytes' > /tmp/sample.wav && PYTHONPATH=src python -m media_workbench.main wave2 --workspace ./workspace --sample /tmp/sample.wav`
- `python -m compileall src`

## Evidence
- Worker engine processes queued jobs to completion.
- API health, job create/read, settings update, and ingest validation behaviors verified by test.
- Derived outputs and DB records remain deterministic.
