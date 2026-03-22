"""CWA Agri integration - config UI plus stage assistant entities."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CARD_RESOURCE_URL, CARD_STATIC_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "select", "button"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CWA Agri integration domain data and bundled dashboard card."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    if not domain_data.get("card_static_registered"):
        card_path = Path(__file__).parent / "www" / "cwa-agri-dashboard.js"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    CARD_STATIC_URL,
                    str(card_path),
                    cache_headers=False,
                )
            ]
        )
        domain_data["card_static_registered"] = True
        domain_data["card_resource_url"] = CARD_RESOURCE_URL
        _LOGGER.info("Registered bundled CWA dashboard card at %s", CARD_STATIC_URL)

    if not domain_data.get("card_resource_registered"):
        frontend.add_extra_js_url(hass, domain_data.get("card_resource_url", CARD_RESOURCE_URL))
        domain_data["card_resource_registered"] = True
        _LOGGER.info("Auto-loaded bundled dashboard card resource: %s", domain_data.get("card_resource_url", CARD_RESOURCE_URL))

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CWA Agri from a config entry."""
    _LOGGER.info("Setting up CWA Agri integration for %s", entry.title)

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = entry
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if result:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
    return result


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options/data change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entries lazily by reload; helper code handles fallback."""
    return True
