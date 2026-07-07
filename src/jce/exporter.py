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


SIDECAR_EXTENSIONS = {
    ".nfo",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".srt",
    ".sub",
    ".idx",
    ".ass",
    ".vtt",
}


def build_export_path(destination: Path, source: Path) -> Path:
    """Preserve the movie folder name under the destination root."""
    return destination / source.parent.name / source.name


def iter_movie_files(video_path: Path) -> list[Path]:
    """The movie file plus sidecar metadata sitting next to it.

    Jellyfin reads title/artwork from local .nfo and image files instead of
    the internet when they are present; without them a hardlinked-only movie
    shows up as a bare filename with no artwork. Sidecars are matched by
    extension in the movie's own folder only, never recursing into
    subfolders (e.g. Extras), so a flat, non-per-movie library layout can't
    accidentally pull in unrelated files.
    """
    folder = video_path.parent
    files = [video_path]
    if not folder.is_dir():
        return files
    for sibling in sorted(folder.iterdir()):
        if sibling == video_path or not sibling.is_file():
            continue
        if sibling.suffix.lower() in SIDECAR_EXTENSIONS:
            files.append(sibling)
    return files


def _paths_overlap(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def ensure_destination_is_isolated(destination: Path, movies: list[Movie]) -> None:
    """Refuse to operate if destination overlaps the real movie library.

    Obsolete-file cleanup only ever deletes inside `destination`, so this is
    the one check standing between a mistyped path and losing real movies.
    """
    for movie in movies:
        source_dir = Path(movie.path).parent
        if _paths_overlap(destination, source_dir):
            raise ExportError(
                "Destination overlaps with the original movie location.\n"
                f"Destination: {destination}\n"
                f"Movie folder: {source_dir}\n"
                "Choose a destination folder that is completely separate from your Jellyfin library."
            )


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
    ensure_destination_is_isolated(destination, movies)
    destination.mkdir(parents=True, exist_ok=True)
    desired: dict[Path, Path] = {}
    for movie in movies:
        for file_path in iter_movie_files(Path(movie.path)):
            desired[build_export_path(destination, file_path)] = file_path
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
                "Source file not found.\n"
                f"Path: {source_path}\n"
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
