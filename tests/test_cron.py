from pathlib import Path
from unittest.mock import patch

import pytest

from jce.cron import CRON_MARKER, CronError, cron_installed, install_cron_job, remove_cron_job


def _crontab_result(stdout: str, returncode: int = 0):
    class Result:
        def __init__(self) -> None:
            self.stdout = stdout
            self.returncode = returncode

    return Result()


def test_install_cron_job_appends_managed_line(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    existing = "0 0 * * * /some/other/job\n"

    with patch("jce.cron.cron_available", return_value=True), patch(
        "jce.cron.subprocess.run"
    ) as run_mock:
        run_mock.side_effect = [
            _crontab_result(existing),
            _crontab_result(""),
        ]
        install_cron_job(config_path, "daily")

    write_call = run_mock.call_args_list[1]
    written_payload = write_call.kwargs["input"]
    assert existing.strip() in written_payload
    assert CRON_MARKER in written_payload
    assert f"jce sync --config {config_path}" in written_payload


def test_install_cron_job_replaces_previous_managed_line(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    existing = f"0 3 * * * jce sync --config /old/path >/dev/null 2>&1 {CRON_MARKER}\n"

    with patch("jce.cron.cron_available", return_value=True), patch(
        "jce.cron.subprocess.run"
    ) as run_mock:
        run_mock.side_effect = [
            _crontab_result(existing),
            _crontab_result(""),
        ]
        install_cron_job(config_path, "daily")

    written_payload = run_mock.call_args_list[1].kwargs["input"]
    assert "/old/path" not in written_payload
    assert str(config_path) in written_payload
    assert written_payload.count(CRON_MARKER) == 1


def test_install_cron_job_without_crontab_raises() -> None:
    with patch("jce.cron.cron_available", return_value=False):
        with pytest.raises(CronError):
            install_cron_job(Path("config.yaml"), "daily")


def test_remove_cron_job_strips_managed_line() -> None:
    existing = f"0 3 * * * jce sync --config /cfg.yaml >/dev/null 2>&1 {CRON_MARKER}\n0 0 * * * /keep/me\n"

    with patch("jce.cron.cron_available", return_value=True), patch(
        "jce.cron.subprocess.run"
    ) as run_mock:
        run_mock.side_effect = [
            _crontab_result(existing),
            _crontab_result(""),
        ]
        remove_cron_job()

    written_payload = run_mock.call_args_list[1].kwargs["input"]
    assert CRON_MARKER not in written_payload
    assert "/keep/me" in written_payload


def test_cron_installed_detects_marker() -> None:
    with patch("jce.cron.read_crontab", return_value=f"* * * * * jce sync {CRON_MARKER}\n"):
        assert cron_installed() is True
    with patch("jce.cron.read_crontab", return_value="* * * * * something-else\n"):
        assert cron_installed() is False
