from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

CRON_MARKER = "# jce managed sync"

SCHEDULE_PRESETS = {
    "hourly": "0 * * * *",
    "every 6 hours": "0 */6 * * *",
    "daily": "0 3 * * *",
    "weekly": "0 3 * * 0",
}


class CronError(RuntimeError):
    """Raised when cron management fails."""


def resolve_schedule(value: str) -> str:
    return SCHEDULE_PRESETS.get(value, value)


def cron_available() -> bool:
    return shutil.which("crontab") is not None


def read_crontab() -> str:
    if not cron_available():
        return ""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def install_cron_job(config_path: Path, schedule: str, command_name: str = "jce") -> None:
    if not cron_available():
        raise CronError(
            "Cannot install cron job automatically.\n"
            "The `crontab` command is not available on this system.\n"
            "Install cron or add the sync command manually."
        )

    cron_line = (
        f"{resolve_schedule(schedule)} {command_name} sync --config {config_path} >/dev/null 2>&1 {CRON_MARKER}"
    )
    lines = [line for line in read_crontab().splitlines() if CRON_MARKER not in line]
    lines.append(cron_line)
    payload = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)


def cron_installed() -> bool:
    return CRON_MARKER in read_crontab()


def remove_cron_job() -> None:
    if not cron_available():
        raise CronError(
            "Cannot remove cron job automatically.\n"
            "The `crontab` command is not available on this system.\n"
            "Remove the sync entry manually from your crontab."
        )

    lines = [line for line in read_crontab().splitlines() if CRON_MARKER not in line]
    payload = "\n".join(lines) + ("\n" if lines else "")
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)
