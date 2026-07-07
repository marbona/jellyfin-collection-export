# AGENTS.md

This repository is intentionally designed to be developed with AI coding assistants.

Human developers and AI agents should follow the same development workflow.

------------------------------------------------------------

# Before writing code

Always read:

1. VISION.md
2. PROJECT.md
3. ARCHITECTURE.md
4. CLAUDE.md

These documents define the project's philosophy and architecture.

Do not implement features that conflict with those documents.

------------------------------------------------------------

# Development philosophy

Prefer many small commits.

Prefer many small pull requests.

Avoid large refactorings.

Implement one feature at a time.

The repository should remain functional after every commit.

------------------------------------------------------------

# Before adding dependencies

Ask yourself:

Can this be implemented using the Python standard library?

If yes, avoid adding a dependency.

If no, explain why the dependency is justified.

------------------------------------------------------------

# Before modifying architecture

Do not introduce new architectural layers unless they clearly simplify the project.

Avoid:

- service locators
- dependency injection frameworks
- plugin systems
- unnecessary abstractions

This project intentionally favors simplicity.

------------------------------------------------------------

# Coding priorities

Priority order:

1. Correctness

2. Readability

3. Maintainability

4. Performance

Do not sacrifice readability for micro-optimizations.

------------------------------------------------------------

# Public API

The CLI is considered the public API.

Avoid breaking command names.

Avoid changing configuration formats without migration support.

------------------------------------------------------------

# Configuration

Configuration files should remain human-readable.

Prefer explicit configuration over implicit behavior.

Never overwrite user configuration automatically.

------------------------------------------------------------

# Logging

Every important operation should produce useful logs.

Never log secrets.

Never log API keys.

------------------------------------------------------------

# Error messages

Every user-facing error should answer:

- What happened?

- Why?

- How can it be fixed?

------------------------------------------------------------

# Testing

Whenever practical:

- add tests

- keep functions testable

- isolate filesystem operations

- isolate Jellyfin communication

------------------------------------------------------------

# Pull Requests

Each Pull Request should have a single purpose.

Examples:

✔ Add doctor command

✔ Improve filesystem validation

✔ Add cron installer

Avoid mixed-purpose pull requests.

------------------------------------------------------------

# Documentation

Whenever functionality changes:

Update documentation.

The documentation is part of the codebase.

Do not leave it behind.

------------------------------------------------------------

# Commit messages

Use Conventional Commits.

Examples:

feat:

fix:

refactor:

docs:

test:

chore:

ci:

------------------------------------------------------------

# Code generation

Generated code should always be:

- formatted

- typed

- documented

- lint clean

Avoid placeholder implementations unless explicitly requested.

------------------------------------------------------------

# If unsure

Do not guess.

Choose the simplest implementation that satisfies the requirements.

If multiple implementations are possible, prefer the one that is easier to maintain in five years.

------------------------------------------------------------

# Project motto

Small.

Reliable.

Predictable.

Unix-like.
