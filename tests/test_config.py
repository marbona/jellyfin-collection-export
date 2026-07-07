from pathlib import Path

from jce.config import AppConfig, ExportConfig, JellyfinConfig, load_config, save_config


def test_save_and_load_config_roundtrip(tmp_path: Path) -> None:
    config = AppConfig(
        jellyfin=JellyfinConfig(url="http://localhost:8096", api_key="secret"),
        exports=[
            ExportConfig(
                name="guest-movies",
                collection_id="abc123",
                collection_name="Guest Movies",
                destination=tmp_path / "export",
                schedule="daily",
            )
        ],
    )

    config_path = tmp_path / "config.yaml"
    save_config(config, config_path)
    loaded = load_config(config_path)

    assert loaded.jellyfin.url == "http://localhost:8096"
    assert loaded.exports[0].collection_id == "abc123"
    assert loaded.exports[0].destination == (tmp_path / "export").resolve()
