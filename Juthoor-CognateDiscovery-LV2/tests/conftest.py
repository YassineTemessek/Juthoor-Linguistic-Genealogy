"""
Shared pytest configuration and markers for the LV2 test suite.
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: mark test as requiring ML models (torch/faiss). Skip with -m 'not slow'.",
    )
