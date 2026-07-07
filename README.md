# jellyfin-collection-export

A small, dependency-light CLI (`jce`) that exports a [Jellyfin](https://jellyfin.org/) Collection into a dedicated folder by creating **hardlinks** to the original movie files.

This makes it possible to share a curated subset of your library — say, a "Guest Movies" collection — through a separate Jellyfin library and a separate Jellyfin user, **without duplicating any disk space** and without ever touching the original files.

```
Original library                 Jellyfin Collection
/mnt/video/Film        ─────►    "Guest Movies"
                                          │
                                          │ hardlinks
                                          ▼
                                 /mnt/video/guest-movies
                                          │
                                          ▼
                                 Dedicated Jellyfin Library
                                          │
                                          ▼
                                 Dedicated Jellyfin User
```

- No movie is copied.
- No additional disk space is used.
- The exported folder always mirrors the content of the selected Jellyfin Collection.
- Jellyfin's API is always the source of truth — the filesystem is never scanned for movie names, only the paths returned by Jellyfin are used.

## Requirements

- Python 3.11+
- Linux
- A running Jellyfin server
- A Jellyfin **administrator API key**
- Source and destination folders on the **same filesystem** (hardlinks cannot cross filesystem/device boundaries)
- A filesystem that supports hardlinks

`jce` actively checks these last two points and refuses to proceed if they are not met.

## Installation

Clone the repository and install it in editable mode inside a virtual environment:

```bash
git clone <this-repo>
cd jellyfin-collection-exporter
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

This installs the `jce` executable via the entry point declared in `pyproject.toml`.

## Getting started

Run the interactive installer:

```bash
jce install
```

The installer will:

1. Ask for the Jellyfin URL (default `http://localhost:8096`) and API key, validating the key immediately.
2. List every Collection available in Jellyfin and let you pick one.
3. Ask for a destination folder, offering to create it if it doesn't exist.
4. Verify that the destination does not overlap with the real movie library, that source and destination are on the same filesystem, and that hardlinks can be created there.
5. Ask for a synchronization interval (`hourly`, `every 6 hours`, `daily`, `weekly`, or a custom cron expression) and, if `cron` is available, install the scheduled job automatically.
6. Optionally run the first synchronization right away.

If a configuration file already exists, `jce install` will ask for confirmation before overwriting it — use `jce reinstall` instead to update an existing setup (see below).

## Commands

| Command | Description |
| --- | --- |
| `jce install` | Run the interactive installation wizard. Refuses to overwrite an existing configuration without confirmation. |
| `jce sync` | Synchronize every configured export: create missing hardlinks, remove obsolete ones, print a summary. |
| `jce sync --dry-run` | Show what `sync` would do, without changing anything on disk. |
| `jce status` | Show collection, destination, movie/hardlink counts, missing files, last sync time and cron status. |
| `jce doctor` | Health check: Jellyfin reachability, API key validity, collection existence, destination existence, destination isolation from the library, filesystem compatibility, hardlink support, cron availability. |
| `jce reinstall` | Re-run the installer, pre-filling every prompt with the current configuration (press Enter to keep a value, including the API key). |
| `jce uninstall` | Remove the managed cron entry and the configuration/state files; optionally remove the exported hardlinks. Use `--yes` to skip every confirmation. |

Every command accepts `--config /path/to/config.yaml` to operate on a configuration file other than the default one, e.g. `jce status --config /path/to/config.yaml`.

## Configuration

Default configuration path:

```text
~/.config/jellyfin-collection-export/config.yaml
```

Example:

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

Synchronization state (last run timestamp and counters) is stored separately, next to the configuration file, in `state.yaml`.

Although the interactive installer currently manages a single export, the configuration format already supports multiple entries under `exports:`, and `jce sync` / `jce status` / `jce doctor` iterate over all of them.

## How synchronization works

1. Read the collection and its movies from the Jellyfin API.
2. Compute the desired state (one folder + hardlink per movie, mirroring the original folder name) from the movie paths returned by Jellyfin.
3. Compare it against the current state of the destination folder.
4. Create missing hardlinks, remove obsolete ones, skip files that are already correctly linked.
5. Prune any directory left empty after removals.
6. Print a summary (`Created`, `Removed`, `Skipped`) and persist it to the state file.

Synchronization is idempotent: running `jce sync` twice in a row produces the same result and does no unnecessary work.

## Safety

The "remove obsolete hardlinks" step only ever deletes files found by scanning inside the configured destination folder — it never looks at, or touches, paths outside of it. The one thing that stands between that and data loss is picking a destination that is genuinely separate from your real Jellyfin library.

To guard against a mistyped path, `jce` refuses to install, reinstall, sync or pass `doctor`'s checks if the destination is equal to, nested inside, or an ancestor of any movie folder belonging to the exported collection. Even so:

- Always point the destination at a dedicated, empty folder outside your library tree (e.g. `/mnt/video/guest-movies`, never `/mnt/video/Film` or a subfolder of it).
- Before trusting a new setup, answer "no" to the installer's "run first synchronization now?" prompt, then run `jce sync --dry-run` yourself and review the planned changes.
- `jce uninstall` only removes exported hardlinks after an explicit confirmation (or `--yes`) — read the printed destination path before confirming.
- Original movie files are never renamed, moved, or written to; `jce` only ever reads them to create hardlinks.

## Scheduling

`jce install` (and `jce reinstall`) can register a cron job automatically, tagged with a managed marker comment so `jce` can find and update it later without touching the rest of your crontab. If `crontab` is not available on the host, `jce` explains how to schedule `jce sync` manually instead.

## Uninstalling

```bash
jce uninstall
```

This removes the managed cron entry and the configuration/state files, and asks whether the exported hardlinks themselves should be deleted (the original movie files are never touched). Pass `--yes` to run non-interactively. The `jce` executable itself is not removed automatically — uninstall the package with:

```bash
pip uninstall jellyfin-collection-export
```

## Development

Install in editable mode and run the test suite:

```bash
python -m pip install -e .
pytest
```

Tests cover configuration round-tripping, the synchronization engine, the Jellyfin API client (HTTP mocked), cron job management (subprocess mocked), and the CLI commands end-to-end (`typer.testing.CliRunner`).

The project favors a small Unix-utility feel: minimal dependencies (Typer, requests, PyYAML), explicit code over clever code, and clear, actionable error messages. See `CLAUDE.md`, `AGENTS.md`, `ARCHITECTURE.md` and `PROJECT.md` for the full design philosophy and specification driving this codebase.

## Project status

This is an early, functional implementation covering the core install/sync/status/doctor/reinstall/uninstall workflow for a single collection. Planned future work includes multiple simultaneous collections, TV show collections, a Docker image, systemd timer support, and packaging for PyPI/Homebrew/Debian/RPM.

## License

MIT
