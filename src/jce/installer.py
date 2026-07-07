from __future__ import annotations

from pathlib import Path

import typer

from .config import AppConfig, ExportConfig, JellyfinConfig, get_config_path, save_config
from .cron import SCHEDULE_PRESETS, install_cron_job
from .exporter import (
    ExportError,
    SyncSummary,
    ensure_destination_is_isolated,
    synchronize_collection,
    verify_hardlink_support,
)
from .jellyfin import JellyfinClient, JellyfinError


def run_install(config_path: Path, existing: AppConfig | None = None) -> Path:
    default_url = existing.jellyfin.url if existing else "http://localhost:8096"
    url = typer.prompt("Jellyfin URL", default=default_url).rstrip("/")

    if existing:
        typer.echo("Press Enter to keep the existing API key.")
        api_key = typer.prompt(
            "API key",
            default=existing.jellyfin.api_key,
            hide_input=True,
            show_default=False,
        )
    else:
        api_key = typer.prompt("API key", hide_input=True)

    client = JellyfinClient(url, api_key)
    client.validate_api_key()

    collections = client.list_collections()
    if not collections:
        raise JellyfinError(
            "No collections found in Jellyfin.\n"
            "Create a collection first, then run `jce install` again."
        )

    typer.echo("Available collections:")
    for index, collection in enumerate(collections, start=1):
        typer.echo(f"{index}. {collection.name}")
    selected_index = typer.prompt("Choose collection number", type=int)
    if selected_index < 1 or selected_index > len(collections):
        raise JellyfinError(
            "Invalid collection selection.\n"
            f"Allowed range: 1-{len(collections)}\n"
            "Run `jce install` again and choose one of the listed collections."
        )
    collection = collections[selected_index - 1]

    existing_export = existing.exports[0] if existing and existing.exports else None

    destination_prompt = (
        typer.prompt("Destination folder", default=str(existing_export.destination))
        if existing_export
        else typer.prompt("Destination folder")
    )
    destination = Path(destination_prompt).expanduser().resolve()
    if destination.exists():
        if not destination.is_dir():
            raise ExportError(
                "Destination path is not a directory.\n"
                f"Path: {destination}\n"
                "Choose an existing directory or a new directory path."
            )
    else:
        if typer.confirm(f"Create destination directory {destination}?", default=True):
            destination.mkdir(parents=True, exist_ok=True)
        else:
            raise ExportError(
                "Destination directory does not exist.\n"
                f"Path: {destination}\n"
                "Create the directory or allow `jce install` to create it."
            )

    typer.echo("Available schedules: " + ", ".join(SCHEDULE_PRESETS.keys()) + ", or a custom cron expression")
    schedule = typer.prompt(
        "Synchronization interval",
        default=existing_export.schedule if existing_export else "daily",
    )

    movies = client.get_collection_movies(collection.id)
    if movies:
        ensure_destination_is_isolated(destination, movies)
        verify_hardlink_support(Path(movies[0].path), destination)

    export = ExportConfig(
        name=existing_export.name if existing_export else collection.name.lower().replace(" ", "-"),
        collection_id=collection.id,
        collection_name=collection.name,
        destination=destination,
        schedule=schedule,
    )
    other_exports = list(existing.exports[1:]) if existing else []
    config = AppConfig(
        jellyfin=JellyfinConfig(url=url, api_key=api_key),
        exports=[export, *other_exports],
    )
    saved_path = save_config(config, config_path)

    if typer.confirm("Install cron entry?", default=True):
        install_cron_job(saved_path, schedule)

    if typer.confirm("Run first synchronization now?", default=True):
        summary: SyncSummary = synchronize_collection(collection.name, destination, movies)
        typer.echo(f"Created: {summary.created}  Removed: {summary.removed}  Skipped: {summary.skipped}")

    return saved_path
