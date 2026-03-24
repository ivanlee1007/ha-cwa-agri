"""CWA Agri integration - config UI plus stage assistant entities."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CROPS,
    CONF_FARM_NAME,
    CONF_HA_TOKEN,
    CONF_HA_URL,
    CONF_REGION,
    DEFAULT_REPORT_SENSOR_ENTITY,
    DOMAIN,
)
from .helpers import get_merged_crops, normalize_ha_url, slugify

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "select", "button"]

DEMO_SENSOR_ENTITY = "sensor.cwa_agri_report"
_CREDENTIALS_FILE = "cwa_credentials.json"


def _write_credentials(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Write ha_url + ha_token to a private file for OpenClaw sync script."""
    creds = {
        "ha_url": normalize_ha_url(entry.data.get(CONF_HA_URL, "")),
        "ha_token": entry.data.get(CONF_HA_TOKEN, ""),
        "farm_name": entry.data.get(CONF_FARM_NAME, ""),
        "region": entry.data.get(CONF_REGION, ""),
        "crops": get_merged_crops(entry),
        "report_sensor_entity": DEFAULT_REPORT_SENSOR_ENTITY,
        # Refresh bridge URL for the dashboard button (HA → OpenClaw)
        "refresh_bridge_url": entry.options.get("refresh_bridge_url", "http://192.168.1.226:18801"),
    }
    path = Path(hass.config.config_dir) / _CREDENTIALS_FILE
    try:
        path.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
        _LOGGER.info("Wrote credentials to %s (NOT exposed in sensor states)", path)
    except OSError as err:
        _LOGGER.warning("Failed to write credentials file: %s", err)


def _ensure_demo_sensor(hass: HomeAssistant) -> None:
    """Create a demo report sensor if it doesn't already exist."""
    if hass.states.get(DEMO_SENSOR_ENTITY):
        return  # already exists (real report or previous demo)

    hass.states.async_set(
        DEMO_SENSOR_ENTITY,
        "demo",
        {
            "icon": "📋",
            "friendly_name": "農業氣象報告（示範用）",
            "farm_name": "示範農場",
            "crop_name": "示範作物",
            "date": "----",
            "issued_at": "----",
            "risk_level": "demo",
            "risk_icon": "📋",
            "risk_text": "此為示範報表，請執行 OpenClaw sync_and_report.js 以取得真實資料",
            "current_weather": "示範資料",
            "temp_min": "--",
            "temp_max": "--",
            "warning_source": "demo",
            "warning_total_active": 0,
            "warning_headline": "",
            "warning_titles": [],
            "warning_priority_actions": [],
            "growth_stage": "—",
            "crops": [],
            "crop_count": 0,
            "weekly_forecast": [
                {"date": "----", "weather": "示範", "minT": "--", "maxT": "--"},
            ],
            "farmer_summary": {
                "headline": "📋 這是示範報表",
                "weather": "安裝完成後，請執行 OpenClaw 的 sync_and_report.js 來推送真實氣象資料",
                "risk_interpretation": "示範模式：此報表由 ha-cwa-agri integration 自動產生，用於預覽卡片樣式",
                "work_window": "等待真實資料推送後會自動更新",
                "fertilizing_advice": "—",
                "spraying_advice": "—",
                "irrigation_advice": "—",
                "note_section": {
                    "title": "📝 安裝說明",
                    "monitoring_risks_text": "1. 確認 OpenClaw 已安裝 openclaw-cwa-skill",
                    "monitoring_items_text": "2. 執行：HA_URL=... HA_TOKEN=... node scripts/sync_and_report.js --all-sites",
                },
            },
        },
        force_update=True,
    )
    _LOGGER.info("Created demo report sensor at %s", DEMO_SENSOR_ENTITY)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up CWA Agri integration domain data and bundled dashboard card."""
    hass.data.setdefault(DOMAIN, {})

    # Dashboard card JS is persisted in .storage/lovelace_resources via /local/ path.
    # See TROUBLESHOOTING.md for details on the JS loading architecture.

    _ensure_demo_sensor(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CWA Agri from a config entry."""
    _LOGGER.info("Setting up CWA Agri integration for %s", entry.title)

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = entry
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Write credentials to private file for OpenClaw sync script (run in executor to avoid blocking event loop)
    await hass.async_add_executor_job(_write_credentials, hass, entry)

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
