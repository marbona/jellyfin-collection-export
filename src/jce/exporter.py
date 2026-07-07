from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .jellyfin import Movie


class ExportError(RuntimeError):
    """Raised when export synchronization fails."""


@dataclass(slots=True)
class SyncSummary:
    collection_name: str
    destination: Path
    created: int = 0
    removed: int = 0
    skipped: int = 0


def build_export_path(destination: Path, source: Path) -> Path:
    """Preserve the movie folder name under the destination root."""
    return destination / source.parent.name / source.name


def ensure_same_filesystem(source: Path, destination: Path) -> None:
    if source.stat().st_dev != destination.stat().st_dev:
        raise ExportError(
            "Cannot create hardlink.\n"
            "Source and destination are on different filesystems.\n"
            f"Choose a destination on the same filesystem as: {source.parent}"
        )


def verify_hardlink_support(source: Path, destination: Path) -> None:
    probe_dir = destination / ".jce-probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    probe_link = probe_dir / source.name
    if probe_link.exists():
        probe_link.unlink()
    try:
        ensure_same_filesystem(source, destination)
        probe_link.hardlink_to(source)
    except OSError as exc:
        raise ExportError(
            "Cannot create hardlink in destination.\n"
            f"Destination: {destination}\n"
            "Check write permissions and hardlink support."
        ) from exc
    finally:
        if probe_link.exists():
            probe_link.unlink()
        if probe_dir.exists():
            probe_dir.rmdir()


def synchronize_collection(
    collection_name: str,
    destination: Path,
    movies: list[Movie],
    dry_run: bool = False,
) -> SyncSummary:
    destination.mkdir(parents=True, exist_ok=True)
    desired = {build_export_path(destination, Path(movie.path)): Path(movie.path) for movie in movies}
    current = {
        path: path
        for path in destination.rglob("*")
        if path.is_file() and ".jce-probe" not in path.parts
    }
    summary = SyncSummary(collection_name=collection_name, destination=destination)

    for path in sorted(current):
        if path not in desired:
            summary.removed += 1
            if not dry_run:
                path.unlink()

    for export_path, source_path in desired.items():
        if not source_path.exists():
            raise ExportError(
                "Source movie file not found.\n"
                f"Movie path: {source_path}\n"
                "Refresh the collection in Jellyfin or remove missing items from the collection."
            )
        if export_path.exists():
            if export_path.stat().st_ino == source_path.stat().st_ino:
                summary.skipped += 1
                continue
            summary.removed += 1
            if not dry_run:
                export_path.unlink()

        summary.created += 1
        if not dry_run:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            ensure_same_filesystem(source_path, destination)
            export_path.hardlink_to(source_path)

    if not dry_run:
        prune_empty_directories(destination)
    return summary


def prune_empty_directories(root: Path) -> None:
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        reverse=True,
    ):
        if any(directory.iterdir()):
            continue
        directory.rmdir()
