"""Config flow for CWA Agri integration."""

import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers import selector

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
            if not user_input.get(CONF_FARM_NAME):
                errors[CONF_FARM_NAME] = "required"
            if not user_input.get(CONF_HA_URL):
                errors[CONF_HA_URL] = "required"
            elif not user_input[CONF_HA_URL].startswith(("http://", "https://")):
                errors[CONF_HA_URL] = "invalid_url"
            if not user_input.get(CONF_HA_TOKEN):
                errors[CONF_HA_TOKEN] = "required"

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
            },
        )

    async def async_step_crops(self, user_input=None):
        """Show crops list with options to add more or finish."""
        errors = {}

        if user_input is not None:
            action = user_input.get("action")
            if action == "add_custom":
                return await self.async_step_add_custom_crop()
            elif action == "remove":
                # Find which remove checkbox was checked
                for key, val in user_input.items():
                    if key.startswith("remove_") and val:
                        idx = int(key.split("_")[1])
                        if 0 <= idx < len(self._crops):
                            self._crops.pop(idx)
                        break
                return await self.async_step_crops()
            elif action == "done":
                if not self._crops:
                    errors["base"] = "need_at_least_one_crop"
                else:
                    self._data[CONF_CROPS] = self._crops
                    return await self.async_step_location()

        return await self._show_crops_form(errors=errors)

    async def _show_crops_form(self, errors=None):
        """Show current crops list with add/remove/done actions."""
        errors = errors or {}

        # Build current crops display and removal options
        crop_options = {}
        for i, crop in enumerate(self._crops):
            stage_name = self._get_stage_display_name(crop["id"], crop["stage"])
            crop_options[vol.Optional(f"remove_{i}", default=False)] = bool

        if not self._crops:
            crops_list_text = "（尚未新增任何作物）"
        else:
            lines = []
            for i, crop in enumerate(self._crops):
                stage_name = self._get_stage_display_name(crop["id"], crop["stage"])
                lines.append(f"{i+1}. {crop['name']} — {stage_name}  [移除]")
            crops_list_text = "\n".join(lines)

        # Actions — use selector dropdown (not vol.In radio)
        crop_options[vol.Required("action")] = selector({"select": {
            "options": [
                {"value": "add_custom", "label": "＋ 新增作物"},
                {"value": "done", "label": "✓ 完成（儲存設定）"},
            ],
            "translation_key": "crop_action",
        }})

        data_schema = vol.Schema(crop_options)

        return self.async_show_form(
            step_id="crops",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "crops_list": crops_list_text,
            },
        )

    async def async_step_add_custom_crop(self, user_input=None):
        """Add a custom crop with free-form name."""
        errors = {}

        if user_input is not None:
            name = user_input.get("crop_name", "").strip()
            stage_id = user_input.get("stage_id", "active")
            if not name:
                errors["crop_name"] = "required"
            else:
                custom_id = f"custom_{uuid.uuid4().hex[:6]}"
                self._crops.append({
                    "id": custom_id,
                    "name": name,
                    "stage": stage_id,
                })
                return await self.async_step_crops()

        stage_options = {s["id"]: s["name"] for s in DEFAULT_STAGES}

        data_schema = vol.Schema({
            vol.Required("crop_name"): str,
            vol.Required("stage_id", default="active"): vol.In(stage_options),
        })

        return self.async_show_form(
            step_id="add_custom_crop",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "stage_options": "\n".join([f"- {s['id']}: {s['name']}" for s in DEFAULT_STAGES]),
            },
        )

    def _get_stage_display_name(self, crop_id, stage_id):
        """Get stage display name for a crop."""
        stages = GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)
        for s in stages:
            if s["id"] == stage_id:
                return s["name"]
        return stage_id

    async def async_step_location(self, user_input=None):
        """Handle optional location settings."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)
            await self.async_set_unique_id(f"cwa_agri_{uuid.uuid4().hex[:8]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._data.get(CONF_FARM_NAME, "CWA 農業報告"),
                data=self._data,
            )

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
        self._crops = list(self._data.get(CONF_CROPS, []))

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle options - same as main flow."""
        errors = {}

        if user_input is not None:
            action = user_input.get("action")
            if action == "add_custom":
                return await self.async_step_add_custom_crop()
            elif action == "remove":
                # Find which remove checkbox was checked
                for key, val in user_input.items():
                    if key.startswith("remove_") and val:
                        idx = int(key.split("_")[1])
                        if 0 <= idx < len(self._crops):
                            self._crops.pop(idx)
                        break
                return await self.async_step_user()
            elif action == "done":
                if not self._crops:
                    errors["base"] = "need_at_least_one_crop"
                else:
                    self._data[CONF_CROPS] = self._crops
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data=self._data,
                    )
                    return self.async_create_entry(title="", data={})

        return await self._show_options_crops_form(errors=errors)

    async def _show_options_crops_form(self, errors=None):
        """Show current crops list for options flow."""
        errors = errors or {}

        crop_options = {}
        if self._crops:
            lines = []
            for i, crop in enumerate(self._crops):
                stage_name = self._get_stage_display_name(crop["id"], crop["stage"])
                lines.append(f"{i+1}. {crop['name']} — {stage_name}")
            crops_list_text = "\n".join(lines)
        else:
            crops_list_text = "（尚未新增任何作物）"

        for i in range(len(self._crops)):
            crop_options[vol.Optional(f"remove_{i}", default=False)] = bool
        crop_options[vol.Required("action")] = selector({"select": {
            "options": [
                {"value": "add_custom", "label": "＋ 新增作物"},
                {"value": "done", "label": "✓ 完成（儲存設定）"},
            ],
            "translation_key": "crop_action",
        }})

        data_schema = vol.Schema(crop_options)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "crops_list": crops_list_text,
            },
        )

    async def async_step_add_custom_crop(self, user_input=None):
        """Add custom crop in options flow."""
        errors = {}

        if user_input is not None:
            name = user_input.get("crop_name", "").strip()
            stage_id = user_input.get("stage_id", "active")
            if not name:
                errors["crop_name"] = "required"
            else:
                custom_id = f"custom_{uuid.uuid4().hex[:6]}"
                self._crops.append({
                    "id": custom_id,
                    "name": name,
                    "stage": stage_id,
                })
                return await self.async_step_user()

        stage_options = {s["id"]: s["name"] for s in DEFAULT_STAGES}
        data_schema = vol.Schema({
            vol.Required("crop_name"): str,
            vol.Required("stage_id", default="active"): vol.In(stage_options),
        })

        return self.async_show_form(
            step_id="add_custom_crop",
            data_schema=data_schema,
            errors=errors,
        )

    def _get_stage_display_name(self, crop_id, stage_id):
        """Get stage display name for a crop."""
        stages = GROWTH_STAGES.get(crop_id, DEFAULT_STAGES)
        for s in stages:
            if s["id"] == stage_id:
                return s["name"]
        return stage_id
