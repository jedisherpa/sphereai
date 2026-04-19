# Developer Setup

## Commands
- Run tests: `PYTHONPATH=src python -m unittest discover -s tests -v`
- Run spike flow: `PYTHONPATH=src python -m media_workbench.main wave2 --workspace ./workspace --sample /tmp/sample.wav`
- Run service: `PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765`

## Notes
- Keep project independent from root `sphere` package.
