from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .utils import expand_path

DEFAULT_CONFIG_PATH = Path("~/.config/jellyfin-collection-export/config.yaml")


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


@dataclass(slots=True)
class JellyfinConfig:
    url: str
    api_key: str


@dataclass(slots=True)
class ExportConfig:
    name: str
    collection_id: str
    collection_name: str
    destination: Path
    schedule: str = "daily"


@dataclass(slots=True)
class AppConfig:
    jellyfin: JellyfinConfig
    exports: list[ExportConfig]


@dataclass(slots=True)
class SyncState:
    last_sync: str
    created: int
    removed: int
    skipped: int


def get_config_path(path: Path | None = None) -> Path:
    return expand_path(path or DEFAULT_CONFIG_PATH)


def get_state_path(path: Path | None = None) -> Path:
    config_path = get_config_path(path)
    return config_path.parent / "state.yaml"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = get_config_path(path)
    if not config_path.exists():
        raise ConfigError(
            "Configuration file not found.\n"
            f"Expected: {config_path}\n"
            "Run `jce install` or pass `--config /path/to/config.yaml`."
        )

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        jellyfin_raw = raw["jellyfin"]
        exports_raw = raw["exports"]
    except KeyError as exc:
        raise ConfigError(
            "Configuration file is invalid.\n"
            "Missing required section.\n"
            "Expected `jellyfin` and `exports` at the top level."
        ) from exc

    if not isinstance(exports_raw, list) or not exports_raw:
        raise ConfigError(
            "Configuration file is invalid.\n"
            "The `exports` section must contain at least one export."
        )

    jellyfin = JellyfinConfig(
        url=str(jellyfin_raw["url"]).rstrip("/"),
        api_key=str(jellyfin_raw["api_key"]),
    )
    exports = [
        ExportConfig(
            name=str(item["name"]),
            collection_id=str(item["collection_id"]),
            collection_name=str(item.get("collection_name", item["name"])),
            destination=expand_path(str(item["destination"])),
            schedule=str(item.get("schedule", "daily")),
        )
        for item in exports_raw
    ]
    return AppConfig(jellyfin=jellyfin, exports=exports)


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    config_path = get_config_path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "jellyfin": {
            "url": config.jellyfin.url,
            "api_key": config.jellyfin.api_key,
        },
        "exports": [
            {
                "name": export.name,
                "collection_id": export.collection_id,
                "collection_name": export.collection_name,
                "destination": str(export.destination),
                "schedule": export.schedule,
            }
            for export in config.exports
        ],
    }
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return config_path


def load_state(path: Path | None = None) -> dict[str, SyncState]:
    state_path = get_state_path(path)
    if not state_path.exists():
        return {}
    raw = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    states: dict[str, SyncState] = {}
    for key, value in raw.items():
        states[key] = SyncState(
            last_sync=str(value["last_sync"]),
            created=int(value["created"]),
            removed=int(value["removed"]),
            skipped=int(value["skipped"]),
        )
    return states


def save_state(states: dict[str, SyncState], path: Path | None = None) -> Path:
    state_path = get_state_path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        key: {
            "last_sync": state.last_sync,
            "created": state.created,
            "removed": state.removed,
            "skipped": state.skipped,
        }
        for key, state in states.items()
    }
    state_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return state_path
