"""Button platform for CWA Agri stage assistant."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LAST_ACK_MONTH, CONF_LAST_ACK_STAGE, DOMAIN, ENTITY_PREFIX
from .helpers import assistant_state, build_updated_options, get_merged_crops, slugify

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up assistant action buttons."""
    crops = get_merged_crops(config_entry)
    entities: list[ButtonEntity] = []
    for crop in crops:
        entities.append(CwaAgriApplySuggestionButton(hass, config_entry, crop))
        entities.append(CwaAgriKeepCurrentStageButton(hass, config_entry, crop))
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
