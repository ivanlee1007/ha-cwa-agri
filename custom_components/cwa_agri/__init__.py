"""CWA Agri integration - config UI plus stage assistant entities."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
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

# Frontend card paths
_CARD_SRC_NAME = "cwa-agri-dashboard.js"
_CARD_DIR_NAME = "cwa_agri"
_CARD_VERSION = "1.4.6"


def _get_card_src(hass: HomeAssistant) -> Path:
    """Path to bundled JS in integration package."""
    return Path(__file__).parent / "www" / _CARD_SRC_NAME


def _get_card_dst(hass: HomeAssistant) -> Path:
    """Target path in HA www/ (served via /local/)."""
    return Path(hass.config.config_dir) / "www" / _CARD_DIR_NAME / _CARD_SRC_NAME


def _get_resources_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.config_dir) / ".storage" / "lovelace_resources"


_CARD_JS_URL = "/cwa_agri_static/cwa-agri-dashboard.js"


def _install_card_js(hass: HomeAssistant) -> bool:
    """Copy JS to www/ for persistence. Returns True if successful."""
    src = _get_card_src(hass)
    dst = _get_card_dst(hass)

    if not src.exists():
        _LOGGER.warning("Card JS not found at %s", src)
        return False

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    _LOGGER.info("Card JS installed to %s", dst)
    return True


def _get_card_js_url(hass: HomeAssistant) -> str:
    """Return card JS URL with mtime-based cache busting."""
    dst = _get_card_dst(hass)
    try:
        mtime = int(dst.stat().st_mtime)
    except (FileNotFoundError, OSError):
        mtime = 0
    return f"{_CARD_JS_URL}?v={mtime}"


def _register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register card resource in lovelace_resources (idempotent, cache-busted)."""
    res_path = _get_resources_path(hass)
    url = _get_card_js_url(hass)

    try:
        with open(res_path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"data": {"resources": [], "items": []}, "key": "lovelace_resources"}

    for arr_name in ("resources", "items"):
        arr = data.get("data", {}).get(arr_name, [])
        existing = [r for r in arr if _CARD_DIR_NAME in r.get("url", "")]
        if existing:
            for r in existing:
                r["url"] = url
        else:
            arr.append({"url": url, "type": "module"})

    data["data"]["resources"] = data.get("data", {}).get("resources", [])
    data["data"]["items"] = data.get("data", {}).get("items", [])
    try:
        with open(res_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as err:
        _LOGGER.warning("Failed to write lovelace_resources: %s", err)


def _uninstall_card(hass: HomeAssistant) -> None:
    """Remove JS file and lovelace_resources entry."""
    dst = _get_card_dst(hass)
    res_path = _get_resources_path(hass)

    # 1. Remove JS file
    if dst.exists():
        dst.unlink()
        _LOGGER.info("Card JS removed: %s", dst)
        # Remove directory if empty
        try:
            dst.parent.rmdir()
        except OSError:
            pass

    # 2. Remove from lovelace_resources
    url = _resource_url()
    try:
        with open(res_path, encoding="utf-8") as f:
            data = json.load(f)
        resources = data.get("data", {}).get("resources", [])
        before = len(resources)
        resources = [r for r in resources if _CARD_DIR_NAME not in r.get("url", "")]
        removed = before - len(resources)
        if removed:
            data["data"]["resources"] = resources
            with open(res_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            _LOGGER.info("Removed %d card resource(s) from lovelace_resources", removed)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass


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

    # Copy JS to www/ for persistence (idempotent, runs every restart)
    await hass.async_add_executor_job(_install_card_js, hass)

    # Register static path so HA serves the JS file directly
    src = _get_card_src(hass)
    if src.exists():
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                _CARD_JS_URL,
                str(src),
                cache_headers=True,
            )
        ])
        # Register with frontend so Lovelace injects it as <script> on every page load
        add_extra_js_url(hass, _get_card_js_url(hass))
        _LOGGER.info("Registered card static path + frontend: %s -> %s", _CARD_JS_URL, src)
    else:
        _LOGGER.warning("Card JS file not found: %s", src)

    _ensure_demo_sensor(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CWA Agri from a config entry."""
    _LOGGER.info("Setting up CWA Agri integration for %s", entry.title)

    # Note: JS registration is done in async_setup, not here,
    # so it runs before any config entry is loaded

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
