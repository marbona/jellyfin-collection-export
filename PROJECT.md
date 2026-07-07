# jellyfin-collection-export

## Overview

jellyfin-collection-export is a command line tool that exports a Jellyfin Collection into a dedicated folder by creating hardlinks to the original movie files.

The goal is to allow sharing only a subset of movies through a separate Jellyfin library without duplicating disk usage.

Example:

Original library

/mnt/video/Film

↓

Jellyfin Collection

↓

Hardlinks

↓

/mnt/video/convitati-share

↓

Dedicated Jellyfin Library

↓

Dedicated Jellyfin User


No movie is copied.

No additional disk space is used.

The exported folder always mirrors the content of the selected Jellyfin Collection.


------------------------------------------------------------

## Requirements

- Python 3.11+
- Linux
- Jellyfin server
- Administrator API Key
- Python virtual environment support available on the host
- Source and destination folders must reside on the same filesystem
- Hardlink support required

The application must refuse configurations where hardlinks cannot be created.


------------------------------------------------------------

## Installation

The application must provide an interactive installer.

Command:

jce install

The installer asks for:

1.
Jellyfin URL

Default:

http://localhost:8096

2.
API Key

The key must be validated immediately.

3.
Collection

The installer retrieves every Collection available through the Jellyfin API.

The user chooses one.

The Collection ID must be stored.

The first implementation may write a single export entry.

The configuration format must still support multiple exports.

4.
Destination folder

The installer asks for a destination folder.

If it does not exist it offers to create it.

Before accepting it must verify:

- same filesystem
- hardlink support

Otherwise installation fails.

5.
Synchronization interval

Available choices:

- hourly
- every 6 hours
- daily
- weekly
- custom cron expression

The installer creates the cron entry automatically.

If cron is not available, the user-facing error must explain how to proceed manually.

6.
Run first synchronization

The installer performs the first synchronization before exiting.


------------------------------------------------------------

## Commands

jce install

Runs the installation wizard.


jce sync

Synchronizes every configured collection.


jce sync --dry-run

Shows planned operations without changing anything.


jce status

Displays configuration and synchronization status.

The latest synchronization timestamp may be stored in a separate state file next to the main configuration.

Example:

Collection:
I convitati di pietra - movie collection

Destination:
/mnt/video/convitati-share

Movies:
20

Hardlinks:
20

Missing:
0

Last synchronization:
2026-07-07 18:10


jce doctor

Checks:

- Jellyfin reachable
- API key valid
- Collection exists
- Destination exists
- Same filesystem
- Hardlink support
- Cron installed


jce reinstall

Runs the installer again preserving existing configuration when possible.


jce uninstall

Removes:

- cron
- configuration
- executable

Must optionally remove exported hardlinks.

The first implementation may provide manual uninstall instructions before full automation is added.


------------------------------------------------------------

## Synchronization

Synchronization must use the Jellyfin API.

Never scan the filesystem looking for movie names.

Every movie path must be retrieved from Jellyfin.

Algorithm:

Read collection

↓

Retrieve movie path

↓

Create hardlink

↓

Remove obsolete hardlinks

↓

Report summary

The current state is discovered by scanning the destination directory.

The desired state is derived only from Jellyfin API paths.


------------------------------------------------------------

## Export layout

Exported folder should preserve movie folders.

Example

convitati-share/

    The Conversation (1974)/
        The Conversation (1974).mkv

    Unforgiven (1992)/
        Unforgiven (1992).mkv

Alongside the movie file, sidecar files sitting in the same source folder are hardlinked too, matched by extension:

- `.nfo`
- images (`.jpg`, `.jpeg`, `.png`, `.webp`)
- subtitles (`.srt`, `.sub`, `.idx`, `.ass`, `.vtt`)

This lets Jellyfin read title and artwork from Radarr-written local metadata instead of falling back to the bare filename when internet metadata lookup is disabled.

Subfolders (e.g. `Extras/`) are never recursed into.


------------------------------------------------------------

## Logging

Log file:

/var/log/jellyfin-collection-export.log

Until file logging exists, the CLI may print human-readable summaries to stdout and stderr.

Example

2026-07-07

Collection:
I convitati di pietra

Movies:
20

Created:
2

Removed:
1

Skipped:
17

Duration:
1.4 seconds


------------------------------------------------------------

## Configuration

Configuration file:

config.yaml

Example

server: http://localhost:8096

api_key: xxxxxxxxxxxxxxxxx

collections:

  - id: xxxxxxxxx

    name: I convitati di pietra - movie collection

    destination: /mnt/video/convitati-share

cron: daily


Although the installer initially configures a single collection,
the internal architecture must support multiple collections.


------------------------------------------------------------

## CLI

Use Typer.

Executable:

jce


------------------------------------------------------------

## Internal modules

cli.py

installer.py

jellyfin.py

exporter.py

config.py

cron.py

utils.py


------------------------------------------------------------

## Nice to have

- colored terminal output
- progress bars
- verbose mode
- debug mode
- dry run mode
- force synchronization
- automatic detection of filesystem root
- automatic validation of hardlink support


------------------------------------------------------------

## Future features

- multiple collections

- export TV collections

- Docker image

- systemd timer instead of cron

- automatic filesystem watcher

- GitHub Releases

- pipx installation

- Homebrew formula

- RPM package

- DEB package


------------------------------------------------------------

## License

MIT


------------------------------------------------------------

## Design principles

- simple

- no unnecessary dependencies

- readable code

- clear error messages

- deterministic behavior

- idempotent synchronization

- safe by default

- production ready
