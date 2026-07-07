# VISION

## Why this project exists

Jellyfin provides excellent media management and user permissions.

However, permissions are granted at the library level.

It is currently not possible to grant a user access to a single Collection while hiding the rest of the library.

Many users solve this by duplicating movie files into another folder.

This wastes disk space and creates synchronization problems.

This project exists to solve that problem.

It exports a Jellyfin Collection into a separate directory using hardlinks.

The exported directory can then be exposed as a dedicated Jellyfin library with its own user permissions.

The result is:

Original Library
        │
        ▼
Jellyfin Collection
        │
        ▼
Hardlink Export
        │
        ▼
Dedicated Jellyfin Library
        │
        ▼
Dedicated User

No files are copied.

No additional storage is required.

The exported library always stays synchronized with the Collection.

------------------------------------------------------------

## Core principles

The Jellyfin Collection is the source of truth.

The filesystem is never scanned looking for movie names.

Movie locations are always retrieved from the Jellyfin API.

The application never modifies the original movie files.

The application never renames movies.

The application never moves movies.

The application never copies movies.

The application only creates or removes hardlinks inside the export directory.

------------------------------------------------------------

## Design goals

The project should remain:

- simple
- predictable
- fast
- safe
- production ready

The synchronization process should always be idempotent.

Running synchronization multiple times without changes should never modify the filesystem.

------------------------------------------------------------

## Non-goals

This project is not a media manager.

This project is not a Jellyfin replacement.

This project is not a backup solution.

This project is not responsible for downloading movies.

This project does not organize media.

This project does one thing only:

Export a Jellyfin Collection as a dedicated filesystem directory.

------------------------------------------------------------

## Target users

This project is intended for:

- Jellyfin administrators
- Home lab users
- Self-hosters
- Linux users
- NAS users
- Proxmox users
- Synology users
- Unraid users
- Docker users

------------------------------------------------------------

## Long-term vision

The long-term goal is to become the standard way of exposing Jellyfin Collections as independent libraries without duplicating media.

Future versions may support:

- TV Shows
- Multiple collections
- Docker images
- systemd timers
- Homebrew
- PyPI
- GitHub Releases

without changing the core philosophy of the project.

------------------------------------------------------------

## One sentence

Keep one movie.

Expose it as many times as needed.
