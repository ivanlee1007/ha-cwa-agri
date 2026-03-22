"""Sensor platform for CWA Agri integration.

Exposes configuration settings as entities for OpenClaw CWA Skill to read.
"""

import json
from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    STATE_UNKNOWN,
)
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
    """Get crop name by ID."""
    for crop in CROPS:
        if crop["id"] == crop_id:
            return crop["name"]
    return crop_id


def stage_name_by_id(crop_id: str, stage_id: str) -> str:
    """Get stage name by ID."""
    stages = GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)
    for stage in stages:
        if stage["id"] == stage_id:
            return stage["name"]
    return stage_id


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="farm_name",
        name="農場名稱",
        icon="mdi:home",
    ),
    SensorEntityDescription(
        key="ha_url",
        name="Home Assistant URL",
        icon="mdi:home-assistant",
    ),
    SensorEntityDescription(
        key="crops_json",
        name="作物設定 (JSON)",
        icon="mdi:seed",
    ),
    SensorEntityDescription(
        key="crops_display",
        name="作物設定",
        icon="mdi:seed",
    ),
    SensorEntityDescription(
        key="latitude",
        name="緯度",
        icon="mdi:latitude",
    ),
    SensorEntityDescription(
        key="longitude",
        name="經度",
        icon="mdi:longitude",
    ),
    SensorEntityDescription(
        key="region",
        name="地區",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="all_settings_json",
        name="所有設定 (JSON)",
        icon="mdi:code-json",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CWA Agri sensors."""
    data = config_entry.data

    # Create entity registry
    entities = []

    # Create main settings sensor
    entities.append(
        CwaAgriSettingsSensor(
            config_entry=config_entry,
            description=SensorEntityDescription(
                key="all_settings_json",
                name="CWA 農業設定",
                icon="mdi:cog",
            ),
        )
    )

    # Create individual crop sensors
    crops = data.get(CONF_CROPS, [])
    for i, crop in enumerate(crops):
        crop_id = crop.get("id", "unknown")
        stage_id = crop.get("stage", "active")

        entities.append(
            CwaAgriCropSensor(
                config_entry=config_entry,
                crop_index=i,
                crop_id=crop_id,
                stage_id=stage_id,
            )
        )

    async_add_entities(entities, update_before_add=True)


class CwaAgriSettingsSensor(SensorEntity):
    """Main settings sensor - exposes all config as JSON."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_settings"
        self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
            configuration_url=self._config_entry.data.get(CONF_HA_URL),
        )

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
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
        """Return the JSON value of all settings."""
        return json.dumps(self._config_entry.data, ensure_ascii=False)


class CwaAgriCropSensor(SensorEntity):
    """Individual crop sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        crop_index: int,
        crop_id: str,
        stage_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._crop_index = crop_index
        self._crop_id = crop_id
        self._stage_id = stage_id
        self._config_entry = config_entry

        crop_name = crop_name_by_id(crop_id)
        stage_name = stage_name_by_id(crop_id, stage_id)

        self.entity_description = SensorEntityDescription(
            key=f"crop_{crop_index}",
            name=f"{crop_name} ({stage_name})",
            icon="mdi:seed",
        )

        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_crop_{crop_index}"
        self._attr_native_value = crop_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
        )

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "crop_id": self._crop_id,
            "crop_name": crop_name_by_id(self._crop_id),
            "stage_id": self._stage_id,
            "stage_name": stage_name_by_id(self._crop_id, self._stage_id),
            "index": self._crop_index,
        }
