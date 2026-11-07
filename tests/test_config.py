import logging

import pytest

from quantum_space_agi import ConfigurationError, Settings


def test_settings_default_to_info_without_loading_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUANTUM_SPACE_AGI_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == logging.INFO


def test_settings_load_log_level_from_environment_explicitly() -> None:
    settings = Settings.from_env({"QUANTUM_SPACE_AGI_LOG_LEVEL": "debug"})

    assert settings.log_level == logging.DEBUG


def test_settings_read_process_environment_only_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUANTUM_SPACE_AGI_LOG_LEVEL", "ERROR")

    assert Settings.from_env().log_level == logging.ERROR


def test_settings_accept_numeric_log_level_from_environment() -> None:
    settings = Settings.from_env({"QUANTUM_SPACE_AGI_LOG_LEVEL": "25"})

    assert settings.log_level == 25


def test_settings_reject_invalid_log_level_with_chained_error() -> None:
    with pytest.raises(ConfigurationError) as error:
        Settings.from_env({"QUANTUM_SPACE_AGI_LOG_LEVEL": "verbose"})

    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.parametrize("level", [-1, True, "INFO"])
def test_settings_reject_invalid_direct_log_level(level: object) -> None:
    with pytest.raises(ConfigurationError):
        Settings(log_level=level)  # type: ignore[arg-type]
