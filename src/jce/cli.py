from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

from .config import (
    AppConfig,
    ConfigError,
    ExportConfig,
    SyncState,
    get_config_path,
    load_config,
    load_state,
    save_state,
)
from .cron import CronError, cron_available, cron_installed
from .exporter import (
    ExportError,
    SyncSummary,
    ensure_same_filesystem,
    synchronize_collection,
    verify_hardlink_support,
)
from .installer import run_install
from .jellyfin import JellyfinClient, JellyfinError

app = typer.Typer(help="Export Jellyfin collections into hardlink-based folders.")


def _client_from_config(config: AppConfig) -> JellyfinClient:
    return JellyfinClient(
        base_url=config.jellyfin.url,
        api_key=config.jellyfin.api_key,
    )


def _render_summary(summary: SyncSummary) -> None:
    typer.echo(f"Collection: {summary.collection_name}")
    typer.echo(f"Destination: {summary.destination}")
    typer.echo(f"Created: {summary.created}")
    typer.echo(f"Removed: {summary.removed}")
    typer.echo(f"Skipped: {summary.skipped}")


def _sync_export(client: JellyfinClient, export: ExportConfig, dry_run: bool) -> SyncSummary:
    collection = client.get_collection(export.collection_id)
    movies = client.get_collection_movies(export.collection_id)
    return synchronize_collection(
        collection_name=collection.name,
        destination=export.destination,
        movies=movies,
        dry_run=dry_run,
    )


def _record_sync_state(config_path: Path | None, export: ExportConfig, summary: SyncSummary) -> None:
    states = load_state(config_path)
    states[export.name] = SyncState(
        last_sync=datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        created=summary.created,
        removed=summary.removed,
        skipped=summary.skipped,
    )
    save_state(states, config_path)


@app.callback()
def main() -> None:
    """CLI entrypoint."""


@app.command()
def install(
    config: Path | None = typer.Option(None, "--config", help="Configuration file path."),
) -> None:
    """Run the interactive installer."""
    config_path = get_config_path(config)
    try:
        saved_path = run_install(config_path)
    except (ConfigError, CronError, ExportError, JellyfinError) as exc:
        raise typer.Exit(code=_fail(str(exc))) from exc
    typer.echo(f"Configuration written to {saved_path}")


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned operations only."),
    config: Path | None = typer.Option(None, "--config", help="Configuration file path."),
) -> None:
    """Synchronize every configured export."""
    try:
        app_config = load_config(config)
        client = _client_from_config(app_config)
        for export in app_config.exports:
            summary = _sync_export(client, export, dry_run=dry_run)
            _render_summary(summary)
            if not dry_run:
                _record_sync_state(config, export, summary)
    except (ConfigError, ExportError, JellyfinError) as exc:
        raise typer.Exit(code=_fail(str(exc))) from exc


@app.command()
def status(
    config: Path | None = typer.Option(None, "--config", help="Configuration file path."),
) -> None:
    """Display current configuration status."""
    try:
        app_config = load_config(config)
        states = load_state(config)
        client = _client_from_config(app_config)
        for export in app_config.exports:
            collection = client.get_collection(export.collection_id)
            movies = client.get_collection_movies(export.collection_id)
            hardlinks = sum(1 for path in export.destination.rglob("*") if path.is_file()) if export.destination.exists() else 0
            missing = max(0, len(movies) - hardlinks)
            typer.echo(f"Collection: {collection.name}")
            typer.echo(f"Destination: {export.destination}")
            typer.echo(f"Movies: {len(movies)}")
            typer.echo(f"Hardlinks: {hardlinks}")
            typer.echo(f"Missing: {missing}")
            typer.echo(f"Last synchronization: {states[export.name].last_sync if export.name in states else 'never'}")
            typer.echo(f"Cron installed: {'yes' if cron_installed() else 'no'}")
            typer.echo("")
    except (ConfigError, JellyfinError) as exc:
        raise typer.Exit(code=_fail(str(exc))) from exc


@app.command()
def doctor(
    config: Path | None = typer.Option(None, "--config", help="Configuration file path."),
) -> None:
    """Check Jellyfin, collection and destination health."""
    try:
        app_config = load_config(config)
        client = _client_from_config(app_config)
        client.validate_api_key()
        typer.echo("Jellyfin reachable: yes")
        typer.echo("API key valid: yes")

        for export in app_config.exports:
            collection = client.get_collection(export.collection_id)
            typer.echo(f"Collection exists: yes ({collection.name})")
            typer.echo(f"Destination exists: {'yes' if export.destination.exists() else 'no'}")
            movies = client.get_collection_movies(export.collection_id)
            if movies and export.destination.exists():
                ensure_same_filesystem(Path(movies[0].path), export.destination)
                verify_hardlink_support(Path(movies[0].path), export.destination)
                typer.echo("Same filesystem: yes")
                typer.echo("Hardlink support: yes")
            else:
                typer.echo("Same filesystem: skipped")
                typer.echo("Hardlink support: skipped")
            typer.echo(f"Cron available: {'yes' if cron_available() else 'no'}")
            typer.echo(f"Cron installed: {'yes' if cron_installed() else 'no'}")
            typer.echo("")
    except (ConfigError, ExportError, JellyfinError) as exc:
        raise typer.Exit(code=_fail(str(exc))) from exc


@app.command()
def reinstall(
    config: Path | None = typer.Option(None, "--config", help="Configuration file path."),
) -> None:
    """Run the installer again."""
    install(config=config)


@app.command()
def uninstall() -> None:
    """Explain manual uninstall steps for now."""
    typer.echo(
        "Uninstall is not automated yet.\n"
        "Remove the managed cron entry, delete the configuration file and optionally delete exported hardlinks."
    )


def _fail(message: str) -> int:
    typer.echo(message, err=True)
    return 1


if __name__ == "__main__":
    app()
