"""Config flow for Image Manager integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_MAX_IMAGES,
    DEFAULT_NAME,
    DEFAULT_MAX_IMAGES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MAX_IMAGES, default=DEFAULT_MAX_IMAGES): vol.All(
            int, vol.Range(min=1, max=100)
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MAX_IMAGES, default=DEFAULT_MAX_IMAGES): vol.All(
            int, vol.Range(min=1, max=100)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate that max_images is within reasonable bounds
    max_images = data[CONF_MAX_IMAGES]
    if not 1 <= max_images <= 100:
        raise InvalidMaxImages

    # Return info that you want to store in the config entry.
    return {
        "title": data[CONF_NAME],
        CONF_NAME: data[CONF_NAME],
        CONF_MAX_IMAGES: max_images,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Image Manager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidMaxImages:
                errors[CONF_MAX_IMAGES] = "invalid_max_images"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> ImageManagerOptionsFlow:
        """Get the options flow for this handler."""
        return ImageManagerOptionsFlow()

    async def async_step_import(self, import_config: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_config)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidMaxImages(HomeAssistantError):
    """Error to indicate invalid max images value."""


class ImageManagerOptionsFlow(OptionsFlowWithReload):
    """Handle Image Manager options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS_SCHEMA,
        )
