from pathlib import Path

import pytest

from jce.exporter import ExportError, synchronize_collection
from jce.jellyfin import Movie


def test_sync_creates_and_skips_existing_hardlinks(tmp_path: Path) -> None:
    source_dir = tmp_path / "source" / "Movie One (2020)"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "Movie One (2020).mkv"
    source_file.write_text("data", encoding="utf-8")

    destination = tmp_path / "export"
    movies = [Movie(id="1", name="Movie One", path=str(source_file))]

    first = synchronize_collection("Collection", destination, movies)
    second = synchronize_collection("Collection", destination, movies)

    export_file = destination / "Movie One (2020)" / "Movie One (2020).mkv"
    assert first.created == 1
    assert export_file.exists()
    assert second.skipped == 1
    assert export_file.stat().st_ino == source_file.stat().st_ino


def test_sync_refuses_destination_inside_library(tmp_path: Path) -> None:
    library_root = tmp_path / "Film"
    movie_dir = library_root / "Movie One (2020)"
    movie_dir.mkdir(parents=True)
    movie_file = movie_dir / "Movie One (2020).mkv"
    movie_file.write_text("data", encoding="utf-8")
    movies = [Movie(id="1", name="Movie One", path=str(movie_file))]

    with pytest.raises(ExportError, match="overlaps with the original movie location"):
        synchronize_collection("Collection", library_root, movies)

    with pytest.raises(ExportError, match="overlaps with the original movie location"):
        synchronize_collection("Collection", movie_dir, movies)

    nested_destination = movie_dir / "export"
    with pytest.raises(ExportError, match="overlaps with the original movie location"):
        synchronize_collection("Collection", nested_destination, movies)

    assert movie_file.exists()
    assert movie_file.read_text(encoding="utf-8") == "data"
