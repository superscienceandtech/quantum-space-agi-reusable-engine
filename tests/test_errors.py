from quantum_space_agi import ConfigurationError, QuantumSpaceError


def test_configuration_error_is_a_package_error() -> None:
    assert issubclass(ConfigurationError, QuantumSpaceError)


def test_package_error_is_an_exception() -> None:
    assert issubclass(QuantumSpaceError, Exception)
