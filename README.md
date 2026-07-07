# jellyfin-collection-export

Small CLI utility that exports a Jellyfin Collection into a dedicated folder by creating hardlinks to the original movie files.

## Commands

```bash
jce install
jce sync
jce sync --dry-run
jce status
jce doctor
```

## Configuration

Default configuration path:

```text
~/.config/jellyfin-collection-export/config.yaml
```

Override it with:

```bash
jce --config /path/to/config.yaml status
```

The configuration format is YAML and supports multiple exports:

```yaml
jellyfin:
  url: http://localhost:8096
  api_key: your-admin-api-key

exports:
  - name: guest-movies
    collection_id: 0123456789abcdef
    collection_name: Guest Movies
    destination: /mnt/video/guest-movies
    schedule: daily
```

## Development

Install in editable mode:

```bash
python -m pip install -e .
```

Run tests:

```bash
pytest
```
