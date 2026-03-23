"""Button platform for CWA Agri stage assistant + refresh report."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_LAST_ACK_MONTH, CONF_LAST_ACK_STAGE, DOMAIN, ENTITY_PREFIX
from .helpers import assistant_state, build_updated_options, get_merged_crops, slugify

_LOGGER = logging.getLogger(__name__)

_CREDENTIALS_FILE = "cwa_credentials.json"


def _read_bridge_url(hass: HomeAssistant) -> str | None:
    """Read refresh bridge URL from private credentials file."""
    try:
        path = Path(hass.config.config_dir) / _CREDENTIALS_FILE
        if path.exists():
            creds = json.loads(path.read_text("utf-8"))
            return creds.get("refresh_bridge_url")
    except Exception:
        pass
    return None


def _read_farm_name(hass: HomeAssistant) -> str | None:
    """Read farm name from private credentials file."""
    try:
        path = Path(hass.config.config_dir) / _CREDENTIALS_FILE
        if path.exists():
            creds = json.loads(path.read_text("utf-8"))
            return creds.get("farm_name")
    except Exception:
        pass
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up assistant action buttons + refresh button."""
    crops = get_merged_crops(config_entry)
    entities: list[ButtonEntity] = []

    # Stage assistant buttons
    for crop in crops:
        entities.append(CwaAgriApplySuggestionButton(hass, config_entry, crop))
        entities.append(CwaAgriKeepCurrentStageButton(hass, config_entry, crop))

    # Refresh report button
    entities.append(CwaAgriRefreshButton(hass, config_entry))

    async_add_entities(entities)


class CwaAgriButtonBase(ButtonEntity):
    """Base button with shared config update helpers."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, crop: dict) -> None:
        self.hass = hass
        self._config_entry = config_entry
        self._crop = crop
        self._crop_slug = slugify(crop["name"])

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
        )

    def _update_crop(self, mutate) -> None:
        crops = get_merged_crops(self._config_entry)
        for crop in crops:
            if slugify(crop["name"]) == self._crop_slug:
                mutate(crop)
                break
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options=build_updated_options(self._config_entry, crops),
        )


class CwaAgriApplySuggestionButton(CwaAgriButtonBase):
    """Apply the current assistant suggestion as the stage."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(hass, config_entry, crop)
        self.entity_id = f"button.cwa_agri_{self._crop_slug}_apply_stage_suggestion"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_apply_stage_suggestion_{self._crop_slug}"
        self._attr_name = f"套用建議階段 - {crop['name']}"
        self._attr_icon = "mdi:check-circle-outline"

    async def async_press(self) -> None:
        info = assistant_state(self._crop)
        month_key = dt_util.now().strftime("%Y-%m")

        def mutate(crop: dict) -> None:
            crop["stage"] = info["suggested_stage_id"]
            crop[CONF_LAST_ACK_STAGE] = info["suggested_stage_id"]
            crop[CONF_LAST_ACK_MONTH] = month_key

        self._update_crop(mutate)
        _LOGGER.info("[CWA Agri] Applied suggested stage '%s' for %s", info["suggested_stage_name"], self._crop["name"])


class CwaAgriKeepCurrentStageButton(CwaAgriButtonBase):
    """Acknowledge the suggestion but keep the current stage for now."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(hass, config_entry, crop)
        self.entity_id = f"button.cwa_agri_{self._crop_slug}_keep_current_stage"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_keep_current_stage_{self._crop_slug}"
        self._attr_name = f"維持目前階段 - {crop['name']}"
        self._attr_icon = "mdi:pause-circle-outline"

    async def async_press(self) -> None:
        info = assistant_state(self._crop)
        month_key = dt_util.now().strftime("%Y-%m")

        def mutate(crop: dict) -> None:
            crop[CONF_LAST_ACK_STAGE] = info["suggested_stage_id"]
            crop[CONF_LAST_ACK_MONTH] = month_key

        self._update_crop(mutate)
        _LOGGER.info("[CWA Agri] Kept current stage for %s while acknowledging suggestion '%s'", self._crop["name"], info["suggested_stage_name"])


class CwaAgriRefreshButton(ButtonEntity):
    """Button to trigger CWA report refresh via OpenClaw bridge."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:refresh"
    entity_id = "button.cwa_agri_refresh"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_refresh_report"
        self._attr_name = "重新整理氣象報告"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
        )

    async def async_press(self) -> None:
        """Call the refresh bridge to trigger OpenClaw report regeneration."""
        bridge_url = _read_bridge_url(self.hass) or "http://192.168.1.226:18801"
        farm_name = _read_farm_name(self.hass) or ""
        session = async_get_clientsession(self.hass)

        payload = {"farm_name": farm_name}
        try:
            async with session.post(f"{bridge_url}/refresh", json=payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    _LOGGER.info("[CWA Agri] Refresh triggered successfully for %s", farm_name)
                else:
                    _LOGGER.warning("[CWA Agri] Refresh bridge error: %s", result.get("error", "unknown"))
        except Exception as err:
            _LOGGER.error("[CWA Agri] Failed to reach refresh bridge at %s: %s", bridge_url, err)
