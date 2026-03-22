"""Sensor platform for CWA Agri integration.

Exposes configuration settings as entities for OpenClaw CWA Skill to read.
"""

import json

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CROPS,
    CONF_FARM_NAME,
    CONF_HA_TOKEN,
    CONF_HA_URL,
    CONF_REGION,
    CROPS,
    DOMAIN,
    ENTITY_PREFIX,
    GROWTH_STAGES,
    DEFAULT_STAGES,
)


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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CWA Agri sensors."""
    data = config_entry.data

    entities = [
        CwaAgriSettingsSensor(config_entry=config_entry),
    ]

    crops = data.get(CONF_CROPS, [])
    for i, crop in enumerate(crops):
        entities.append(
            CwaAgriCropSensor(
                config_entry=config_entry,
                crop_index=i,
                crop_id=crop.get("id", "unknown"),
                stage_id=crop.get("stage", "active"),
                crop_name=crop.get("name"),
            )
        )

    async_add_entities(entities, update_before_add=True)


class CwaAgriSettingsSensor(SensorEntity):
    """Main sensor — exposes all config as JSON for OpenClaw to read."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self.entity_description = SensorEntityDescription(
            key="all_settings_json",
            name="CWA 農業設定",
            icon="mdi:cog",
        )
        self._attr_unique_id = (
            f"{ENTITY_PREFIX}_{config_entry.entry_id}_settings"
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
            configuration_url=self._config_entry.data.get(CONF_HA_URL),
        )

    @property
    def extra_state_attributes(self):
        data = self._config_entry.data
        return {
            CONF_FARM_NAME: data.get(CONF_FARM_NAME, ""),
            CONF_HA_URL: data.get(CONF_HA_URL, ""),
            CONF_HA_TOKEN: data.get(CONF_HA_TOKEN, ""),
            CONF_LATITUDE: data.get(CONF_LATITUDE, ""),
            CONF_LONGITUDE: data.get(CONF_LONGITUDE, ""),
            CONF_REGION: data.get(CONF_REGION, ""),
            CONF_CROPS: json.dumps(data.get(CONF_CROPS, []), ensure_ascii=False),
        }

    @property
    def native_value(self):
        return json.dumps(self._config_entry.data, ensure_ascii=False)


class CwaAgriCropSensor(SensorEntity):
    """Per-crop sensor showing crop name and current stage."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        crop_index: int,
        crop_id: str,
        stage_id: str,
        crop_name: str = None,
    ) -> None:
        self._crop_index = crop_index
        self._crop_id = crop_id
        self._stage_id = stage_id
        self._config_entry = config_entry

        name = crop_name or crop_name_by_id(crop_id)
        stage_name = stage_name_by_id(crop_id, stage_id)

        self.entity_description = SensorEntityDescription(
            key=f"crop_{crop_index}",
            name=f"{name}（{stage_name}）",
            icon="mdi:seed",
        )
        self._attr_unique_id = (
            f"{ENTITY_PREFIX}_{config_entry.entry_id}_crop_{crop_index}"
        )
        self._attr_native_value = name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
        )

    @property
    def extra_state_attributes(self):
        return {
            "crop_id": self._crop_id,
            "crop_name": crop_name_by_id(self._crop_id),
            "stage_id": self._stage_id,
            "stage_name": stage_name_by_id(self._crop_id, self._stage_id),
            "index": self._crop_index,
        }
