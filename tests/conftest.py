"""Gemeinsame Test-Einstellungen."""

import pytest


@pytest.fixture
def custom_integrations(enable_custom_integrations):
    """Aktiviert die Integration für Tests mit Home Assistant."""
    return
