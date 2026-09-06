"""Smoke tests for the P0/P1 package skeleton."""


def test_package_imports() -> None:
    """The project package is importable before numerical work begins."""
    import scramjet1d

    assert scramjet1d.__name__ == "scramjet1d"
