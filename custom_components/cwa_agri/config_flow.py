"""Config flow for CWA Agri integration."""

import json
import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback

from .const import (
    CONF_CROPS,
    CONF_FARM_NAME,
    CONF_HA_TOKEN,
    CONF_HA_URL,
    CONF_REGION,
    CROPS,
    DOMAIN,
    GROWTH_STAGES,
    DEFAULT_STAGES,
)


@config_entries.HANDLERS.register(DOMAIN)
class CwaAgriConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CWA Agri."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}
        self._crops: list[dict[str, str]] = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate basic info
            if not user_input.get(CONF_FARM_NAME):
                errors[CONF_FARM_NAME] = "required"
            if not user_input.get(CONF_HA_URL):
                errors[CONF_HA_URL] = "required"
            elif not user_input[CONF_HA_URL].startswith(("http://", "https://")):
                errors[CONF_HA_URL] = "invalid_url"
            if not user_input.get(CONF_HA_TOKEN):
                errors[CONF_HA_TOKEN] = "required"

            # Test HA connection
            if not errors and not user_input.get("_skip_test"):
                from homeassistant.helpers.aiohttp_client import async_get_clientsession
                import aiohttp

                session = async_get_clientsession(self.hass)
                ha_url = user_input[CONF_HA_URL].rstrip("/")

                try:
                    async with session.get(
                        f"{ha_url}/api/",
                        headers={"Authorization": f"Bearer {user_input[CONF_HA_TOKEN]}"},
                        timeout=10,
                    ) as resp:
                        if resp.status != 200:
                            errors[CONF_HA_TOKEN] = "auth_failed"
                except aiohttp.ClientError:
                    errors[CONF_HA_URL] = "connection_failed"
                except Exception:
                    errors[CONF_HA_URL] = "unknown_error"

            if not errors:
                self._data.update(user_input)
                return await self.async_step_crops()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_FARM_NAME, default=self._data.get(CONF_FARM_NAME, "")): str,
                vol.Required(CONF_HA_URL, default=self._data.get(CONF_HA_URL, "http://homeassistant:8123")): str,
                vol.Required(CONF_HA_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "farm_name": "農場名稱（用於識別此設定）",
                "ha_url": "Home Assistant URL",
                "ha_token": "Home Assistant 長期訪問令牌",
                "token_help": "設定 → 個人 → 長期訪問令牌",
            },
        )

    async def async_step_crops(self, user_input=None):
        """Handle crops and growth stages selection."""
        errors = {}

        if user_input is not None:
            # Parse crop selections
            selected_crops = []
            for crop in CROPS:
                crop_id = crop["id"]
                if user_input.get(f"crop_{crop_id}"):
                    stage_id = user_input.get(f"stage_{crop_id}", "active")
                    selected_crops.append({
                        "id": crop_id,
                        "name": crop["name"],
                        "stage": stage_id,
                    })

            if not selected_crops:
                errors["base"] = "select_at_least_one_crop"

            if not errors:
                self._data[CONF_CROPS] = selected_crops
                return await self.async_step_location()

        # Build crop selection schema dynamically
        crop_fields = {}
        for crop in CROPS:
            crop_id = crop["id"]
            stages = GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)
            stage_options = {s["id"]: s["name"] for s in stages}

            crop_fields[
                vol.Required(f"crop_{crop_id}", default=bool(self._crops and any(c.get("id") == crop_id for c in self._crops)))
            ] = bool
            crop_fields[
                vol.Optional(f"stage_{crop_id}", default=self._get_default_stage(crop_id))
            ] = vol.In(stage_options)

        data_schema = vol.Schema(crop_fields)

        return self.async_show_form(
            step_id="crops",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "help": "選擇種植的作物種類及其生長階段",
            },
        )

    async def async_step_location(self, user_input=None):
        """Handle optional location settings."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)

            # Generate unique ID for this config entry
            await self.async_set_unique_id(f"cwa_agri_{uuid.uuid4().hex[:8]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._data.get(CONF_FARM_NAME, "CWA 農業報告"),
                data=self._data,
            )

        # Pre-fill with HA's own location if available
        defaults = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
            CONF_REGION: "",
        }

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_LATITUDE, default=defaults[CONF_LATITUDE]): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=defaults[CONF_LONGITUDE]): vol.Coerce(float),
                vol.Optional(CONF_REGION, default=defaults[CONF_REGION]): str,
            }
        )

        return self.async_show_form(
            step_id="location",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "help": "選擇農場位置（用於獲取當地天氣資訊）",
            },
        )

    def _get_default_stage(self, crop_id: str) -> str:
        """Get default stage for a crop."""
        for c in self._crops:
            if c.get("id") == crop_id:
                return c.get("stage", "active")
        stages = GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)
        return stages[0]["id"] if stages else "active"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return CwaAgriOptionsFlow(config_entry)


class CwaAgriOptionsFlow(config_entries.OptionsFlow):
    """Handle options for CWA Agri."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._data = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle options - re-use user flow."""
        errors = {}

        if user_input is not None:
            # Validate and update
            self._data.update(user_input)
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=self._data,
            )
            return self.async_create_entry(title="", data={})

        # Build current options schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_FARM_NAME, default=self._data.get(CONF_FARM_NAME, "")): str,
                vol.Required(CONF_HA_URL, default=self._data.get(CONF_HA_URL, "")): str,
                vol.Required(CONF_HA_TOKEN, default=self._data.get(CONF_HA_TOKEN, "")): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
