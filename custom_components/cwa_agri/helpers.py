"""Helper utilities for CWA Agri integration."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
import hashlib
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify as ha_slugify

from .const import (
    ASSIST_MONTH_MAP,
    CONF_CROPS,
    CONF_LAST_ACK_MONTH,
    CONF_LAST_ACK_STAGE,
    CONF_PROFILE,
    CONF_STAGE_MODE,
    DEFAULT_STAGE_MODE,
    DEFAULT_STAGES,
    GROWTH_STAGES,
    PROFILE_GENERIC,
    PROFILE_KEYWORDS,
    PROFILE_LABELS,
    STAGE_MODE_ASSIST,
)


def slugify(value: str) -> str:
    """Create a stable slug for entity ids."""
    original = value or ""
    slug = ha_slugify(original)
    if slug:
        return slug

    value = original.strip().lower()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^a-z0-9_\-]", "", value)
    if value:
        return value

    digest = hashlib.md5(original.encode("utf-8")).hexdigest()[:8]
    return f"crop_{digest}"


def detect_crop_profile(crop_name: str) -> str:
    """Best-effort crop profile detection from a free-form crop name."""
    lowered = crop_name.strip().lower()
    for profile, keywords in PROFILE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                return profile
    return PROFILE_GENERIC


def get_stage_choices(profile: str | None) -> list[dict[str, str]]:
    """Return stage choices for a profile."""
    return GROWTH_STAGES.get(profile or PROFILE_GENERIC, DEFAULT_STAGES)


def stage_name_by_id(profile: str | None, stage_id: str | None) -> str:
    """Convert stage id to display name."""
    if stage_id is None:
        return "未設定"
    for stage in get_stage_choices(profile):
        if stage["id"] == stage_id:
            return stage["name"]
    return stage_id


def stage_id_by_name(profile: str | None, stage_name: str | None) -> str | None:
    """Convert stage display name back to id."""
    if stage_name is None:
        return None
    for stage in get_stage_choices(profile):
        if stage["name"] == stage_name:
            return stage["id"]
    return None


def initial_stage_id(profile: str, when: datetime | None = None) -> str:
    """Pick a reasonable default stage based on month + profile."""
    when = when or dt_util.now()
    suggested = ASSIST_MONTH_MAP.get(profile, ASSIST_MONTH_MAP[PROFILE_GENERIC]).get(when.month)
    valid_ids = {stage["id"] for stage in get_stage_choices(profile)}
    if suggested in valid_ids:
        return suggested
    return get_stage_choices(profile)[0]["id"]


def normalize_crop_record(raw: dict[str, Any], when: datetime | None = None) -> dict[str, Any]:
    """Normalize one crop record into the new v2/v2.1 shape."""
    name = str(raw.get("name") or raw.get("id") or "").strip()
    if not name:
        return {}

    profile = raw.get(CONF_PROFILE) or detect_crop_profile(name)
    valid_stage_ids = {stage["id"] for stage in get_stage_choices(profile)}
    stage = raw.get("stage")
    if stage not in valid_stage_ids:
        stage = initial_stage_id(profile, when=when)

    return {
        "name": name,
        CONF_PROFILE: profile,
        "stage": stage,
        CONF_STAGE_MODE: raw.get(CONF_STAGE_MODE, DEFAULT_STAGE_MODE),
        CONF_LAST_ACK_STAGE: raw.get(CONF_LAST_ACK_STAGE),
        CONF_LAST_ACK_MONTH: raw.get(CONF_LAST_ACK_MONTH),
    }


def parse_crop_names(text: str, existing_crops: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Parse textarea crop names into normalized crop records."""
    existing_map = {
        str(crop.get("name", "")).strip(): crop
        for crop in (existing_crops or [])
        if str(crop.get("name", "")).strip()
    }

    parts = re.split(r"[\n,]+", text or "")
    ordered_names = OrderedDict()
    for part in parts:
        name = part.strip()
        if name:
            ordered_names[name] = True

    crops: list[dict[str, Any]] = []
    for name in ordered_names.keys():
        previous = existing_map.get(name, {"name": name})
        normalized = normalize_crop_record(previous)
        if normalized:
            crops.append(normalized)

    return crops


def crop_names_to_text(crops: list[dict[str, Any]]) -> str:
    """Convert crop records back into textarea form."""
    return "\n".join(crop.get("name", "") for crop in crops if crop.get("name"))


def get_merged_crops(config_entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return normalized crops from options first, then data."""
    raw_crops = config_entry.options.get(CONF_CROPS, config_entry.data.get(CONF_CROPS, []))
    return [crop for crop in (normalize_crop_record(item) for item in raw_crops) if crop]


def get_crop_by_slug(config_entry: ConfigEntry, crop_slug: str) -> dict[str, Any] | None:
    """Find a crop by slug."""
    for crop in get_merged_crops(config_entry):
        if slugify(crop["name"]) == crop_slug:
            return crop
    return None


def build_updated_options(config_entry: ConfigEntry, crops: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a new options payload preserving unknown options keys."""
    options = dict(config_entry.options)
    options[CONF_CROPS] = crops
    return options


def profile_label(profile: str | None) -> str:
    """Human label for a crop profile."""
    return PROFILE_LABELS.get(profile or PROFILE_GENERIC, PROFILE_LABELS[PROFILE_GENERIC])


def suggest_stage(crop: dict[str, Any], when: datetime | None = None) -> dict[str, Any]:
    """Provide a lightweight seasonal stage suggestion."""
    when = when or dt_util.now()
    profile = crop.get(CONF_PROFILE) or detect_crop_profile(crop.get("name", ""))
    stage_id = ASSIST_MONTH_MAP.get(profile, ASSIST_MONTH_MAP[PROFILE_GENERIC]).get(when.month)
    valid_ids = {stage["id"] for stage in get_stage_choices(profile)}
    if stage_id not in valid_ids:
        stage_id = initial_stage_id(profile, when=when)

    confidence = "medium" if profile != PROFILE_GENERIC else "low"
    return {
        "profile": profile,
        "profile_label": profile_label(profile),
        "suggested_stage_id": stage_id,
        "suggested_stage_name": stage_name_by_id(profile, stage_id),
        "confidence": confidence,
        "reason": f"依 {when.month} 月季節節奏與「{profile_label(profile)}」通用週期推估",
    }


def assistant_state(crop: dict[str, Any], when: datetime | None = None) -> dict[str, Any]:
    """Return assistant state, suggestion, and ack status for one crop."""
    when = when or dt_util.now()
    suggestion = suggest_stage(crop, when=when)
    current_stage = crop.get("stage")
    current_stage_name = stage_name_by_id(crop.get(CONF_PROFILE), current_stage)
    stage_mode = crop.get(CONF_STAGE_MODE, DEFAULT_STAGE_MODE)
    ack_stage = crop.get(CONF_LAST_ACK_STAGE)
    ack_month = crop.get(CONF_LAST_ACK_MONTH)

    if stage_mode != STAGE_MODE_ASSIST:
        status = "手動模式"
    elif current_stage == suggestion["suggested_stage_id"]:
        status = "一致"
    elif ack_stage == suggestion["suggested_stage_id"] and ack_month == when.strftime("%Y-%m"):
        status = "已確認"
    else:
        status = "待確認"

    return {
        **suggestion,
        "status": status,
        "current_stage_id": current_stage,
        "current_stage_name": current_stage_name,
        "stage_mode": stage_mode,
        "ack_stage": ack_stage,
        "ack_month": ack_month,
    }
