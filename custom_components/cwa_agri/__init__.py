"""CWA Agri integration - provides config UI and exposes settings for OpenClaw CWA Skill."""

import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CROPS,
    CONF_FARM_NAME,
    CONF_HA_TOKEN,
    CONF_HA_URL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_REGION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CWA Agri from a config entry."""
    _LOGGER.info("Setting up CWA Agri integration for %s", entry.title)

    # Store the integration data in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward to sensor platform to create entities
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading CWA Agri integration")

    # Unload sensor entities
    result = await hass.config_entries.async_unload_entries(entry, ["sensor"])

    if entry.entry_id in hass.data.get(DOMAIN, {}):
        del hass.data[DOMAIN][entry.entry_id]

    return result


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate a config entry to a new version."""
    # Handle migration logic here if needed
    return True
