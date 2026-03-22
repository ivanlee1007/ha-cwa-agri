"""CWA Agri integration - provides config UI and exposes settings for OpenClaw CWA Skill."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CWA Agri from a config entry."""
    _LOGGER.info("Setting up CWA Agri integration for %s", entry.title)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward to sensor + select platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "select"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading CWA Agri integration")

    result = await hass.config_entries.async_unload_entries(
        entry, ["sensor", "select"]
    )

    if entry.entry_id in hass.data.get(DOMAIN, {}):
        del hass.data[DOMAIN][entry.entry_id]

    return result


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate a config entry to a new version."""
    return True
