"""Select platform for CWA Agri — crop growth stage dropdowns.

Exposes one dropdown (SelectEntity) per crop so users can change the
growth stage directly from the HA dashboard without going into settings.
"""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CROPS,
    CROPS,
    DOMAIN,
    ENTITY_PREFIX,
    GROWTH_STAGES,
    DEFAULT_STAGES,
)

_LOGGER = logging.getLogger(__name__)


def crop_name_by_id(crop_id: str) -> str:
    """Get crop name by ID (preset or custom)."""
    for crop in CROPS:
        if crop["id"] == crop_id:
            return crop["name"]
    return crop_id


def stage_choices_for_crop(crop_id: str) -> list[dict]:
    """Get available stage choices for a crop."""
    return GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)


def stage_name_by_id(crop_id: str, stage_id: str) -> str:
    """Get stage display name by crop and stage ID."""
    stages = stage_choices_for_crop(crop_id)
    for s in stages:
        if s["id"] == stage_id:
            return s["name"]
    return stage_id


class CwaAgriStageSelect(SelectEntity):
    """Dropdown for selecting a crop's growth stage.

    Appears as a dropdown in the HA UI. When the user changes it,
    the new value is stored in the entity state and OpenClaw's
    sync_ha_config.js reads it via the HA API.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        crop_index: int,
        crop_id: str,
        crop_name: str,
        current_stage_id: str,
    ) -> None:
        self.hass = hass
        self._config_entry = config_entry
        self._crop_index = crop_index
        self._crop_id = crop_id
        self._crop_name = crop_name

        safe = "".join(c for c in crop_name if c.isalnum() or c in "_-")
        self._attr_unique_id = (
            f"{ENTITY_PREFIX}_{config_entry.entry_id}_stage_{crop_index}_{safe}"
        )
        self.entity_id = f"select.cwa_agri_{safe}_stage"

        stages = stage_choices_for_crop(crop_id)
        self._options = [s["name"] for s in stages]
        self._stage_ids = [s["id"] for s in stages]

        self._attr_name = f"CWA 作物階段 - {crop_name}"
        self._attr_icon = "mdi:tree-outline"

        current_name = stage_name_by_id(crop_id, current_stage_id)
        self._attr_current_option = current_name

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
        )

    @property
    def options(self) -> list[str]:
        """Available dropdown options (stage names)."""
        return self._options

    @property
    def current_option(self) -> str | None:
        """Current selected stage name."""
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Handle user selecting a new stage from the dropdown."""
        self._attr_current_option = option
        self.async_write_ha_state()
        _LOGGER.info(
            "[CWA Agri] Crop '%s' stage changed to '%s'",
            self._crop_name,
            option,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up crop stage dropdowns."""
    crops = config_entry.data.get(CONF_CROPS, [])

    entities = [
        CwaAgriStageSelect(
            hass=hass,
            config_entry=config_entry,
            crop_index=i,
            crop_id=crop.get("id", "unknown"),
            crop_name=crop.get("name", crop_name_by_id(crop.get("id", "unknown"))),
            current_stage_id=crop.get("stage", "active"),
        )
        for i, crop in enumerate(crops)
    ]

    async_add_entities(entities, update_before_add=True)
    _LOGGER.info("[CWA Agri] Registered %d stage dropdown(s)", len(entities))
