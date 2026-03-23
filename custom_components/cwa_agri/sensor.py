"""Sensor platform for CWA Agri integration."""

from __future__ import annotations

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
    DEFAULT_REPORT_SENSOR_ENTITY,
    ENTITY_PREFIX,
    DOMAIN,
)
from .helpers import assistant_state, get_merged_crops, normalize_ha_url, profile_label, slugify, stage_name_by_id


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CWA Agri sensors."""
    crops = get_merged_crops(config_entry)
    entities: list[SensorEntity] = [CwaAgriSettingsSensor(config_entry)]

    for crop in crops:
        entities.append(CwaAgriCropSensor(config_entry, crop))
        entities.append(CwaAgriStageAssistantSensor(config_entry, crop))

    async_add_entities(entities, update_before_add=True)


class CwaAgriBaseEntity(SensorEntity):
    """Base entity with shared device metadata."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CWA 農業整合",
            manufacturer="OpenClaw",
            model="CWA Agri Integration",
            configuration_url=self._config_entry.data.get(CONF_HA_URL),
        )


class CwaAgriSettingsSensor(CwaAgriBaseEntity):
    """Expose the merged configuration as JSON for OpenClaw to read."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__(config_entry)
        self.entity_description = SensorEntityDescription(
            key="all_settings_json",
            name="CWA 農業設定",
            icon="mdi:cog",
        )
        farm_slug = slugify(config_entry.data.get(CONF_FARM_NAME, config_entry.entry_id))
        self.entity_id = f"sensor.cwa_agri_{farm_slug}_settings"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_settings"

    def _safe_config(self) -> dict:
        """Config without sensitive fields - safe to expose in HA states."""
        data = dict(self._config_entry.data)
        data.pop(CONF_HA_TOKEN, None)  # never expose token
        data[CONF_HA_URL] = normalize_ha_url(data.get(CONF_HA_URL))
        data[CONF_CROPS] = get_merged_crops(self._config_entry)
        return data

    @property
    def extra_state_attributes(self):
        data = self._safe_config()
        return {
            CONF_FARM_NAME: data.get(CONF_FARM_NAME, ""),
            CONF_LATITUDE: data.get(CONF_LATITUDE, ""),
            CONF_LONGITUDE: data.get(CONF_LONGITUDE, ""),
            CONF_REGION: data.get(CONF_REGION, ""),
            CONF_CROPS: json.dumps(data.get(CONF_CROPS, []), ensure_ascii=False),
            "crop_count": len(data.get(CONF_CROPS, [])),
            "report_sensor_entity": DEFAULT_REPORT_SENSOR_ENTITY,
            "sync_ready": True,
        }

    @property
    def native_value(self):
        return json.dumps(self._safe_config(), ensure_ascii=False)


class CwaAgriCropSensor(CwaAgriBaseEntity):
    """Compact per-crop status sensor."""

    def __init__(self, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(config_entry)
        self._crop = crop
        crop_slug = slugify(crop["name"])
        self.entity_id = f"sensor.cwa_agri_{crop_slug}"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_crop_{crop_slug}"
        self.entity_description = SensorEntityDescription(
            key=f"crop_{crop_slug}",
            name=f"作物 - {crop['name']}",
            icon="mdi:seed",
        )

    @property
    def native_value(self):
        return stage_name_by_id(self._crop.get("profile"), self._crop.get("stage"))

    @property
    def extra_state_attributes(self):
        return {
            "crop_name": self._crop["name"],
            "profile": self._crop.get("profile"),
            "profile_label": profile_label(self._crop.get("profile")),
            "stage_id": self._crop.get("stage"),
            "stage_name": stage_name_by_id(self._crop.get("profile"), self._crop.get("stage")),
            "stage_mode": self._crop.get("stage_mode"),
        }


class CwaAgriStageAssistantSensor(CwaAgriBaseEntity):
    """Show seasonal stage suggestion + confirmation status."""

    def __init__(self, config_entry: ConfigEntry, crop: dict) -> None:
        super().__init__(config_entry)
        self._crop = crop
        crop_slug = slugify(crop["name"])
        self.entity_id = f"sensor.cwa_agri_{crop_slug}_stage_assistant"
        self._attr_unique_id = f"{ENTITY_PREFIX}_{config_entry.entry_id}_stage_assistant_{crop_slug}"
        self.entity_description = SensorEntityDescription(
            key=f"stage_assistant_{crop_slug}",
            name=f"階段助手 - {crop['name']}",
            icon="mdi:assistant",
        )

    @property
    def native_value(self):
        return assistant_state(self._crop)["status"]

    @property
    def extra_state_attributes(self):
        info = assistant_state(self._crop)
        return {
            "crop_name": self._crop["name"],
            "current_stage": info["current_stage_name"],
            "current_stage_id": info["current_stage_id"],
            "suggested_stage": info["suggested_stage_name"],
            "suggested_stage_id": info["suggested_stage_id"],
            "confidence": info["confidence"],
            "reason": info["reason"],
            "stage_mode": info["stage_mode"],
            "profile": info["profile"],
            "profile_label": info["profile_label"],
            "ack_stage": info["ack_stage"],
            "ack_month": info["ack_month"],
        }
