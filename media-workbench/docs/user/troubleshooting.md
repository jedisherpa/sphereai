# Troubleshooting

## Server not starting
- Verify port availability.
- Check Python version >= 3.10.

## Ingest errors
- Confirm `media_kind` is `image` or `audio`.
- Confirm extension is allowed and file exists.

## Jobs stuck
- Restart service; recovery requeues `running` jobs to `retrying`.
