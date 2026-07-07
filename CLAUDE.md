# CLAUDE.md

This file contains the development guidelines for AI coding agents working on this repository.

The goal is to keep the codebase consistent, maintainable and production ready.

------------------------------------------------------------

# General philosophy

This project should feel like a small Unix utility.

It should be:

- simple
- predictable
- readable
- easy to debug
- easy to package
- easy to maintain

Never over-engineer solutions.

Prefer explicit code over clever code.

Readability always wins.

------------------------------------------------------------

# Python version

Minimum supported version:

Python 3.11

Always use modern Python features.

------------------------------------------------------------

# Dependencies

Keep dependencies to an absolute minimum.

Preferred libraries:

- Typer
- requests
- PyYAML
- Rich

Rich is optional for the first usable version.

Avoid frameworks.

Do not introduce dependencies unless they provide significant value.

------------------------------------------------------------

# Code style

Always use:

- type hints
- dataclasses where appropriate
- pathlib instead of os.path whenever possible

Functions should remain small.

Classes should exist only when they simplify the code.

Avoid unnecessary abstractions.

------------------------------------------------------------

# Project organization

Business logic must never live inside the CLI.

CLI commands should only call services.

Filesystem code belongs in exporter.py.

HTTP code belongs in jellyfin.py.

Configuration belongs in config.py.

------------------------------------------------------------

# Error handling

Every error message should explain:

- what happened

- why

- how to fix it

Avoid cryptic exceptions.

Never expose stack traces to end users unless running in debug mode.

------------------------------------------------------------

# Logging

Every important operation should be logged.

Use structured logging whenever practical.

Log:

- synchronization start
- synchronization end
- created links
- removed links
- skipped links
- errors

------------------------------------------------------------

# Synchronization

Synchronization must always be idempotent.

Running the synchronization twice should produce exactly the same result.

Never recreate existing hardlinks.

Never touch original movie files.

Never rename original movie files.

Never move original movie files.

------------------------------------------------------------

# Filesystem

Hardlinks are the preferred export method.

Before creating hardlinks always verify:

- source exists
- destination filesystem matches
- destination is writable

If hardlinks cannot be created, fail with a clear explanation.

------------------------------------------------------------

# Jellyfin

The Jellyfin API is the source of truth.

Never search the filesystem looking for movie names.

Never guess movie locations.

Always retrieve movie paths from the Jellyfin API.

------------------------------------------------------------

# CLI

The executable is:

jce

Commands should remain short.

Output should be human friendly.

Use colors only where they improve readability.

------------------------------------------------------------

# Configuration

Use YAML.

Configuration should remain human editable.

Never overwrite configuration without confirmation.

Keep runtime state separate from user-edited configuration whenever possible.

------------------------------------------------------------

# Testing

Design every module so it can be tested independently.

Separate business logic from external dependencies.

Mock Jellyfin during tests.

If the execution environment cannot provide venv, pip or test tooling, keep the code compileable and leave clear host-side test instructions.

------------------------------------------------------------

# Documentation

Public functions should contain concise docstrings.

Complex algorithms should include comments explaining WHY.

Avoid comments that simply explain WHAT the code already says.

------------------------------------------------------------

# Performance

Movie collections are usually small.

Optimize for readability first.

Optimize performance only when there is measurable benefit.

------------------------------------------------------------

# Security

Never log API keys.

Never print secrets.

Always sanitize user input.

------------------------------------------------------------

# Backwards compatibility

Avoid breaking configuration formats.

If configuration changes, provide migration logic.

------------------------------------------------------------

# Pull requests

Prefer many small pull requests over one large pull request.

Each PR should solve one problem.

------------------------------------------------------------

# Release quality

Every release should be installable and usable.

The main branch should always remain functional.

Prefer a smaller working command set over placeholder automation that is not yet reliable.

------------------------------------------------------------

# Future vision

The application should eventually support:

- multiple collections
- TV Shows
- Docker
- systemd timers
- PyPI
- Homebrew
- GitHub Releases

The architecture should allow these features without requiring major rewrites.
