# Architecture

## Philosophy

The project follows a simple architecture with a clear separation of responsibilities.

Every module should have a single responsibility.

The application must be easy to understand, easy to test and easy to extend.

No business logic should exist inside the CLI.

The CLI only invokes services.


------------------------------------------------------------

# High level architecture

                CLI
                 │
                 ▼
          Application Layer
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 Jellyfin API          Configuration
      │                     │
      └──────────┬──────────┘
                 ▼
         Synchronization Engine
                 │
                 ▼
        Filesystem Operations
                 │
                 ▼
             Hardlinks


------------------------------------------------------------

# Modules

cli.py

Entry point.

Contains Typer commands.

No business logic.


------------------------------------------------------------

installer.py

Interactive installation wizard.

Responsibilities:

- validate API key
- discover collections
- validate filesystem
- create destination folder
- create cron job
- write configuration
- launch first synchronization


------------------------------------------------------------

jellyfin.py

Wrapper around Jellyfin REST API.

Responsible for:

- authentication
- collection discovery
- retrieving collection content
- retrieving movie paths

No filesystem logic.


------------------------------------------------------------

exporter.py

Core synchronization engine.

Responsibilities:

- compare collection with destination
- create hardlinks
- remove obsolete hardlinks
- generate summary

This is the heart of the application.


------------------------------------------------------------

config.py

Read and write YAML configuration.

Configuration validation.


------------------------------------------------------------

cron.py

Create

Update

Remove cron entries.


------------------------------------------------------------

utils.py

Shared helper functions.

No business logic.


------------------------------------------------------------

# Synchronization algorithm

Read configuration

↓

Connect to Jellyfin

↓

Load collection

↓

Retrieve every movie path

↓

Build desired state

↓

Scan destination folder

↓

Build current state

↓

Compare states

↓

Create missing hardlinks

↓

Delete obsolete hardlinks

↓

Generate report


------------------------------------------------------------

# Idempotency

Synchronization must be idempotent.

Running sync multiple times without changes must never modify anything.

Expected output:

Created: 0

Removed: 0

Skipped: 20


------------------------------------------------------------

# Filesystem

Only hardlinks are supported.

Never copy movie files.

Never move movie files.

Never rename original movie files.


------------------------------------------------------------

# Error handling

Every error should explain:

What happened

Why

How to fix it

Bad:

Permission denied

Good:

Cannot create hardlink.

Source and destination are on different filesystems.

Choose a destination inside:

/mnt/video


------------------------------------------------------------

# Logging

Every synchronization must generate:

Start time

End time

Duration

Collection

Movies processed

Created

Removed

Skipped

Errors


------------------------------------------------------------

# Testing

Every module should be independently testable.

Filesystem operations should be isolated.

Jellyfin communication should be mockable.


------------------------------------------------------------

# Coding style

Python 3.11+

Type hints everywhere.

Dataclasses where appropriate.

Small functions.

Readable code over clever code.


------------------------------------------------------------

# External dependencies

Keep dependencies minimal.

Preferred:

Typer

requests

PyYAML

Rich

Avoid large frameworks.


------------------------------------------------------------

# Future architecture

The synchronization engine should support multiple exporters.

Current:

Filesystem Hardlink Exporter

Possible future:

Symlink Exporter

Copy Exporter

ZIP Exporter

Cloud Exporter

The CLI should remain unchanged.
