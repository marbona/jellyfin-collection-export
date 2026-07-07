from pathlib import Path

import pytest
from typer.testing import CliRunner

from jce.cli import app
from jce.config import load_config
from jce.jellyfin import Collection, JellyfinClient, Movie

runner = CliRunner()


@pytest.fixture(autouse=True)
def _fake_jellyfin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    source_dir = tmp_path / "source" / "Movie One (2020)"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "Movie One (2020).mkv"
    source_file.write_text("data", encoding="utf-8")

    monkeypatch.setattr(JellyfinClient, "validate_api_key", lambda self: None)
    monkeypatch.setattr(
        JellyfinClient,
        "list_collections",
        lambda self: [Collection(id="abc123", name="Guest Movies")],
    )
    monkeypatch.setattr(
        JellyfinClient,
        "get_collection",
        lambda self, collection_id: Collection(id=collection_id, name="Guest Movies"),
    )
    monkeypatch.setattr(
        JellyfinClient,
        "get_collection_movies",
        lambda self, collection_id: [Movie(id="1", name="Movie One", path=str(source_file))],
    )
    return source_file


def _run_install(config_path: Path, dest: Path, install_cron: str = "n", first_sync: str = "y") -> None:
    result = runner.invoke(
        app,
        ["install", "--config", str(config_path)],
        input="\n".join(
            [
                "",  # Jellyfin URL -> default
                "secret",  # API key
                "1",  # collection number
                str(dest),  # destination folder
                "y",  # create destination directory
                "",  # schedule -> default daily
                install_cron,  # install cron entry
                first_sync,  # run first synchronization now
            ]
        )
        + "\n",
    )
    assert result.exit_code == 0, result.output


def test_install_writes_config_and_runs_first_sync(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    dest = tmp_path / "export"

    _run_install(config_path, dest)

    config = load_config(config_path)
    assert config.exports[0].collection_id == "abc123"
    assert config.exports[0].destination == dest.resolve()
    assert (dest / "Movie One (2020)" / "Movie One (2020).mkv").exists()


def test_install_refuses_to_overwrite_without_confirmation(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    dest = tmp_path / "export"
    _run_install(config_path, dest)

    result = runner.invoke(
        app,
        ["install", "--config", str(config_path)],
        input="n\n",
    )
    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_reinstall_prefills_existing_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    dest = tmp_path / "export"
    _run_install(config_path, dest)

    result = runner.invoke(
        app,
        ["reinstall", "--config", str(config_path)],
        input="\n".join(
            [
                "",  # keep existing URL
                "",  # keep existing API key
                "1",  # collection number
                "",  # keep existing destination
                "",  # keep existing schedule
                "n",  # install cron entry
                "n",  # run first synchronization now
            ]
        )
        + "\n",
    )
    assert result.exit_code == 0, result.output

    config = load_config(config_path)
    assert len(config.exports) == 1
    assert config.exports[0].destination == dest.resolve()
    assert config.jellyfin.api_key == "secret"


def test_uninstall_removes_config_state_and_hardlinks(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    dest = tmp_path / "export"
    _run_install(config_path, dest)
    assert config_path.exists()

    result = runner.invoke(
        app,
        ["uninstall", "--config", str(config_path), "--yes"],
    )
    assert result.exit_code == 0, result.output
    assert not config_path.exists()
    assert not dest.exists()


def test_status_reports_missing_hardlinks(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    dest = tmp_path / "export"
    _run_install(config_path, dest, first_sync="n")

    result = runner.invoke(app, ["status", "--config", str(config_path)])
    assert result.exit_code == 0, result.output
    assert "Movies: 1" in result.output
    assert "Missing: 1" in result.output
