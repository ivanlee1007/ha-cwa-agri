"""Config flow for CWA Agri integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_CROPS, CONF_FARM_NAME, CONF_HA_TOKEN, CONF_HA_URL, CONF_REGION, DOMAIN, CWA_COUNTIES, CWA_COUNTY_TO_REGION
from .helpers import crop_names_to_text, get_merged_crops, normalize_ha_url, parse_crop_names

_LOGGER = logging.getLogger(__name__)

CONF_CROP_NAMES_TEXT = "crop_names_text"



@config_entries.HANDLERS.register(DOMAIN)
class CwaAgriConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CWA Agri."""

    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Collect only the basic connection information."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                if not user_input.get(CONF_FARM_NAME):
                    errors[CONF_FARM_NAME] = "required"
                if not user_input.get(CONF_HA_URL):
                    errors[CONF_HA_URL] = "required"
                elif not user_input[CONF_HA_URL].startswith(("http://", "https://")):
                    errors[CONF_HA_URL] = "invalid_url"
                if not user_input.get(CONF_HA_TOKEN):
                    errors[CONF_HA_TOKEN] = "required"

                if not errors:
                    user_input[CONF_HA_URL] = normalize_ha_url(user_input.get(CONF_HA_URL))
                    self._data.update(user_input)
                    return await self.async_step_location()
            except Exception as err:  # pragma: no cover - defensive
                _LOGGER.exception("CWA Agri config error: %s", err)
                errors["base"] = "unknown_error"

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
        )

    async def async_step_location(self, user_input: dict[str, Any] | None = None):
        """Collect location + initial crop list in one clean step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                crop_text = user_input.pop(CONF_CROP_NAMES_TEXT, "")
                self._data.update(user_input)
                county = user_input.get(CONF_REGION, "").strip()
                if not county:
                    errors[CONF_REGION] = "required"
                elif county not in CWA_COUNTY_TO_REGION:
                    errors[CONF_REGION] = "invalid_region"
                else:
                    # 存縣市名稱，API 呼叫時再映射到地區
                    self._data[CONF_REGION] = county
                self._data[CONF_HA_URL] = normalize_ha_url(self._data.get(CONF_HA_URL))
                self._data[CONF_CROPS] = parse_crop_names(crop_text)

                if not errors:
                    unique_seed = f"{self._data.get(CONF_HA_URL, '')}::{self._data.get(CONF_FARM_NAME, '')}"
                    unique_id = f"cwa_agri_{uuid.uuid5(uuid.NAMESPACE_URL, unique_seed).hex[:12]}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=self._data.get(CONF_FARM_NAME, "CWA 農業報告"),
                        data=self._data,
                    )
            except Exception as err:  # pragma: no cover - defensive
                _LOGGER.exception("CWA Agri location step error: %s", err)
                errors["base"] = "unknown_error"

        defaults = {
            CONF_REGION: self._data.get(CONF_REGION, ""),
            CONF_CROP_NAMES_TEXT: "",
        }

        data_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=defaults[CONF_REGION]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CWA_COUNTIES,
                        translation_key=CONF_REGION,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_CROP_NAMES_TEXT,
                    default=defaults[CONF_CROP_NAMES_TEXT],
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiple=True)
                ),
            }
        )

        return self.async_show_form(
            step_id="location",
            data_schema=data_schema,
            errors=errors,
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Expose one single, much simpler maintenance page."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                crop_text = user_input.pop(CONF_CROP_NAMES_TEXT, "")
                current_crops = get_merged_crops(self._config_entry)
                new_crops = parse_crop_names(crop_text, existing_crops=current_crops)

                new_data = dict(self._config_entry.data)
                new_data.update(user_input)
                # Ensure cleared optional fields are overwritten (HA may omit
                # empty Optional keys from user_input, leaving stale values).
                county = user_input.get(CONF_REGION, "").strip()
                if county and county in CWA_COUNTY_TO_REGION:
                    new_data[CONF_REGION] = county  # 存縣市名稱
                elif not county:
                    errors[CONF_REGION] = "required"
                new_data[CONF_HA_URL] = normalize_ha_url(new_data.get(CONF_HA_URL))

                if not errors:
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data=new_data,
                        options={CONF_CROPS: new_crops},
                    )
                return self.async_create_entry(title="", data={})
            except Exception as err:  # pragma: no cover - defensive
                _LOGGER.exception("CWA Agri options error: %s", err)
                errors["base"] = "unknown_error"

        current_crops = get_merged_crops(self._config_entry)
        crop_text_default = crop_names_to_text(current_crops)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_FARM_NAME, default=self._config_entry.data.get(CONF_FARM_NAME, "")): str,
                vol.Required(CONF_HA_URL, default=self._config_entry.data.get(CONF_HA_URL, "http://homeassistant:8123")): str,
                vol.Required(CONF_HA_TOKEN, default=self._config_entry.data.get(CONF_HA_TOKEN, "")): str,
                vol.Required(CONF_REGION, default=self._config_entry.data.get(CONF_REGION, "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CWA_COUNTIES,
                        translation_key=CONF_REGION,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_CROP_NAMES_TEXT, default=crop_text_default): selector.TextSelector(
                    selector.TextSelectorConfig(multiple=True)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
