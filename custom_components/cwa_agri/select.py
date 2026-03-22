"""Select platform for CWA Agri."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_LAST_ACK_MONTH,
    CONF_LAST_ACK_STAGE,
    CONF_STAGE_MODE,
    DEFAULT_STAGE_MODE,
    DOMAIN,
    ENTITY_PREFIX,
    STAGE_MODE_ASSIST,
    STAGE_MODE_MANUAL,
)
from .helpers import (
    build_updated_options,
    get_merged_crops,
    get_stage_choices,
    slugify,
    stage_id_by_name,
    stage_name_by_id,
)

_LOGGER = logging.getLogger(__name__)
MODE_LABELS = {
    STAGE_MODE_MANUAL: "手動",
    STAGE_MODE_ASSIST: "半自動",
}
MODE_VALUES = {value: key for key, value in MODE_LABELS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up crop stage + mode dropdowns."""
    crops = get_merged_crops(config_entry)
    entities: list[SelectEntity] = []
    for crop in crops:
        entities.append(CwaAgriStageSelect(hass, config_entry, crop))
        entities.append(CwaAgriStageModeSelect(hass, config_entry, crop))
    async_add_entities(entities, update_before_add=True)
    _LOGGER.info("[CWA Agri] Registered %d select entities", len(entities))


class CwaAgriSelectBase(SelectEntity):
    """Base select entity with persistence helpers."""

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

    def _updated_crops(self, mutate):
        crops = get_merged_crops(self._config_entry)
        for crop in crops:
            if slugify(crop["name"]) == self._crop_slug:
                mutate(crop)
                break
        return crops

    def _save_crops(self, crops):
        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options=build_updated_options(self._config_entry, crops),
        )


class CwaAgriStageSelect(CwaAgriSelectBase):
    """Dropdown for current growth stage."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(hass, config_entry, crop)
        self.entity_id = f"select.cwa_agri_{self._crop_slug}_stage"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_stage_{self._crop_slug}"
        self._attr_name = f"作物階段 - {crop['name']}"
        self._attr_icon = "mdi:sprout"
        self._options_map = get_stage_choices(crop.get("profile"))
        self._attr_options = [stage["name"] for stage in self._options_map]

    @property
    def current_option(self) -> str | None:
        return stage_name_by_id(self._crop.get("profile"), self._crop.get("stage"))

    @property
    def extra_state_attributes(self):
        return {
            "crop_name": self._crop["name"],
            "crop_slug": self._crop_slug,
            "profile": self._crop.get("profile"),
        }

    async def async_select_option(self, option: str) -> None:
        stage_id = stage_id_by_name(self._crop.get("profile"), option)
        if not stage_id:
            return

        crops = self._updated_crops(
            lambda crop: crop.update(
                {
                    "stage": stage_id,
                    CONF_LAST_ACK_STAGE: None,
                    CONF_LAST_ACK_MONTH: None,
                }
            )
        )
        self._save_crops(crops)
        _LOGGER.info("[CWA Agri] Crop '%s' stage changed to '%s'", self._crop["name"], option)


class CwaAgriStageModeSelect(CwaAgriSelectBase):
    """Dropdown for manual vs assist mode."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(hass, config_entry, crop)
        self.entity_id = f"select.cwa_agri_{self._crop_slug}_stage_mode"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_stage_mode_{self._crop_slug}"
        self._attr_name = f"階段模式 - {crop['name']}"
        self._attr_icon = "mdi:tune-variant"
        self._attr_options = list(MODE_VALUES.keys())

    @property
    def current_option(self) -> str | None:
        mode = self._crop.get(CONF_STAGE_MODE, DEFAULT_STAGE_MODE)
        return MODE_LABELS.get(mode, MODE_LABELS[STAGE_MODE_ASSIST])

    @property
    def extra_state_attributes(self):
        return {
            "crop_name": self._crop["name"],
            "crop_slug": self._crop_slug,
        }

    async def async_select_option(self, option: str) -> None:
        mode_value = MODE_VALUES.get(option)
        if not mode_value:
            return

        crops = self._updated_crops(lambda crop: crop.update({CONF_STAGE_MODE: mode_value}))
        self._save_crops(crops)
        _LOGGER.info("[CWA Agri] Crop '%s' stage mode changed to '%s'", self._crop["name"], option)
