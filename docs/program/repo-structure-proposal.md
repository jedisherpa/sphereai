# Repository Structure Proposal

```text
sphereai/
  apps/
    web/                  # React/Vite UI
    helper/               # Optional desktop helper
  services/
    api/                  # FastAPI local service
    workers/
      ocr/
      asr/
      diarization/
      enrichment/
  packages/
    shared-types/
    shared-config/
  data-schemas/
    sqlite/
    json/
  scripts/
    dev/
    build/
    package/
    benchmark/
  docs/
    program/
    research/
    architecture/
    adrs/
    perf/
    hardening/
    release/
  reports/
    wave-0/
    wave-1/
    ...
```

## Runtime Data Layout (User Workspace)
```text
<workspace_root>/
  raw/images/YYYY/MM/DD/
  raw/audio/YYYY/MM/DD/
  derived/ocr/<asset-id>/
  derived/transcripts/<asset-id>/
  derived/clips/<asset-id>/
  derived/enrichment/<asset-id>/
  exports/
  cache/models/
  cache/temp/
  logs/
  app.db
```

## Ownership Map (Initial)
- `services/api`: Backend/API Team
- `services/workers/*`: Pipeline teams
- `apps/web`: Frontend Team
- `apps/helper`: Desktop Helper Team
- `data-schemas`: Data/Storage Team
- `scripts/build|package`: Build/Release Team
