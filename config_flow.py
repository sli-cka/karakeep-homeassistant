from __future__ import annotations

import logging
import voluptuous as vol
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponseError, ClientConnectorError, ClientTimeout, InvalidURL

from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .api import KarakeepClient

_LOGGER = logging.getLogger(__name__)


class KarakeepConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Karakeep config flow and reconfiguration."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return KarakeepOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle initial config flow initiated by the user."""
        _LOGGER.debug("Starting Karakeep config flow - user step")
        return await self._async_handle_config_step("user", user_input)

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Handle reconfiguration of an existing Karakeep entry.

        Exposed via the UI (Reconfigure menu) to update URL/token/scan_interval.
        """
        _LOGGER.debug("Starting Karakeep config flow - reconfigure step")
        if not self._async_current_entries():
            _LOGGER.debug("Reconfigure requested but no existing entries found, aborting")
            return self.async_abort(reason="no_existing_config")

        # For now we assume a single entry; if multiple are ever supported,
        # Home Assistant will pass the correct entry_id context.
        entry = self._async_current_entries()[0]
        return await self._async_handle_config_step("reconfigure", user_input, entry)

    async def _async_handle_config_step(
        self,
        step_id: str,
        user_input,
        existing_entry: config_entries.ConfigEntry | None = None,
    ) -> FlowResult:
        """Shared handler for initial setup and reconfiguration.

        - Validates URL format.
        - Tests connectivity & auth.
        - For 'user': creates new entry.
        - For 'reconfigure': updates existing config entry.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input.get(CONF_URL, "").strip()
            token = user_input.get(CONF_TOKEN, "").strip()
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            _LOGGER.debug(
                "Processing %s step input: url=%s, token_len=%s, scan_interval=%s",
                step_id,
                url,
                len(token) if token else 0,
                scan_interval,
            )

            # Validate URL
            try:
                parsed = urlparse(url)
                _LOGGER.debug(
                    "URL parse result - scheme=%s, netloc=%s, path=%s",
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                )

                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    _LOGGER.error(
                        "Invalid URL format for %s step: %s", step_id, url
                    )
                    errors["base"] = "invalid_url_format"
                else:
                    # Normalize URL (without trailing slash)
                    normalized_url = url.rstrip("/")
                    session = async_get_clientsession(self.hass)
                    client = KarakeepClient(normalized_url, token, session)

                    try:
                        _LOGGER.debug(
                            "Testing connection to Karakeep API at %s (%s step)",
                            normalized_url,
                            step_id,
                        )
                        await client.async_get_stats()
                        _LOGGER.info(
                            "Successfully validated Karakeep configuration (%s step)",
                            step_id,
                        )

                        data = {
                            CONF_URL: normalized_url,
                            CONF_TOKEN: token,
                            CONF_SCAN_INTERVAL: scan_interval,
                        }

                        # Prevent duplicate configuration for the same URL when creating
                        for existing in self._async_current_entries():
                            if (
                                existing_entry is None
                                or existing.entry_id != existing_entry.entry_id
                            ) and existing.data.get(CONF_URL) == normalized_url:
                                _LOGGER.debug(
                                    "Found existing Karakeep entry (%s) with same URL=%s; aborting",
                                    existing.entry_id,
                                    normalized_url,
                                )
                                return self.async_abort(reason="already_configured")

                        if step_id == "reconfigure" and existing_entry is not None:
                            _LOGGER.debug(
                                "Updating existing Karakeep entry_id=%s with new data",
                                existing_entry.entry_id,
                            )
                            self.hass.config_entries.async_update_entry(
                                existing_entry,
                                data=data,
                                options={
                                    **existing_entry.options,
                                    CONF_SCAN_INTERVAL: scan_interval,
                                },
                            )
                            return self.async_abort(reason="reconfigure_successful")

                        _LOGGER.debug(
                            "Creating new Karakeep config entry (user step)"
                        )
                        return self.async_create_entry(
                            title="Karakeep",
                            data=data,
                        )

                    except ClientConnectorError as err:
                        _LOGGER.debug("Connection error details: %s", err)
                        _LOGGER.error("Connection error during %s step: %s", step_id, err)
                        errors["base"] = "cannot_connect"
                    except ClientResponseError as err:
                        _LOGGER.debug(
                            "Response error details - Status: %s, Message: %s",
                            err.status,
                            err.message,
                        )
                        _LOGGER.error(
                            "Invalid response from API during %s step: %s",
                            step_id,
                            err,
                        )
                        if err.status == 401:
                            errors["base"] = "invalid_auth"
                        elif err.status == 404:
                            errors["base"] = "invalid_api_path"
                        else:
                            errors["base"] = "api_error"
                    except ClientTimeout as err:
                        _LOGGER.debug("Timeout error details: %s", err)
                        _LOGGER.error(
                            "Timeout connecting to API during %s step", step_id
                        )
                        errors["base"] = "timeout_error"
                    except ClientError as err:
                        _LOGGER.debug(
                            "Client error type: %s, details: %s",
                            type(err).__name__,
                            err,
                        )
                        _LOGGER.error(
                            "Client error during %s step: %s", step_id, err
                        )
                        errors["base"] = "client_error"
                    except InvalidURL as err:
                        _LOGGER.debug("Invalid URL error details: %s", err)
                        _LOGGER.error(
                            "Invalid URL during %s step: %s", step_id, err
                        )
                        errors["base"] = "invalid_url"
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug(
                            "Unexpected error type during %s step: %s",
                            step_id,
                            type(err).__name__,
                        )
                        _LOGGER.exception(
                            "Unexpected error during %s step: %s", step_id, err
                        )
                        errors["base"] = "unknown"

            except ValueError as err:
                _LOGGER.debug("URL parsing ValueError details: %s", err)
                _LOGGER.error(
                    "URL parsing error for %s step with url=%s", step_id, url
                )
                errors["base"] = "invalid_url_format"

        # Build schema with defaults (for reconfigure use existing values)
        if existing_entry is not None:
            default_url = existing_entry.data.get(CONF_URL, "")
            default_token = existing_entry.data.get(CONF_TOKEN, "")
            default_interval = existing_entry.options.get(
                CONF_SCAN_INTERVAL,
                existing_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        else:
            default_url = ""
            default_token = ""
            default_interval = DEFAULT_SCAN_INTERVAL

        _LOGGER.debug(
            "Showing %s form with defaults: url=%s, token_len=%s, scan_interval=%s; errors=%s",
            step_id,
            default_url,
            len(default_token) if default_token else 0,
            default_interval,
            errors,
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=default_url): str,
                vol.Required(CONF_TOKEN, default=default_token): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=default_interval,
                ): vol.All(cv.positive_int, vol.Range(min=30)),
            }
        )

        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
        )


class KarakeepOptionsFlow(config_entries.OptionsFlow):
    """Handle Karakeep options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug("Updating options with: %s", user_input)
            return self.async_create_entry(title="", data=user_input)

        # Get current scan interval from options, fall back to data if not in options
        current_scan_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        
        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=current_scan_interval,
            ): vol.All(cv.positive_int, vol.Range(min=30))
        }

        _LOGGER.debug("Creating options form schema")
        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
