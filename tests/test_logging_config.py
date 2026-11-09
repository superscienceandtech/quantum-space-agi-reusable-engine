import logging

from quantum_space_agi import Settings, configure_logging, get_logger


def test_get_logger_returns_package_namespaced_logger() -> None:
    logger = get_logger("tests")

    assert logger.name == "quantum_space_agi.tests"


def test_configure_logging_is_opt_in_and_does_not_mutate_root_logger() -> None:
    root_logger = logging.getLogger()
    root_handlers = tuple(root_logger.handlers)
    root_level = root_logger.level
    package_logger = logging.getLogger("quantum_space_agi")
    previous_level = package_logger.level
    previous_handlers = tuple(package_logger.handlers)
    previous_propagate = package_logger.propagate

    try:
        configured_logger = configure_logging(Settings(log_level=logging.DEBUG))

        assert configured_logger is package_logger
        assert configured_logger.level == logging.DEBUG
        assert tuple(configured_logger.handlers) == previous_handlers
        assert configured_logger.propagate is previous_propagate
        assert tuple(root_logger.handlers) == root_handlers
        assert root_logger.level == root_level
    finally:
        package_logger.setLevel(previous_level)
        package_logger.handlers[:] = list(previous_handlers)
        package_logger.propagate = previous_propagate
