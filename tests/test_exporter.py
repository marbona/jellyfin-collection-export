from pathlib import Path

from jce.exporter import synchronize_collection
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
