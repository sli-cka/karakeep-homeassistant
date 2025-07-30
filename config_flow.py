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
    VERSION = 1
    
    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return KarakeepOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initiated by the user."""
        _LOGGER.debug("Starting Karakeep config flow - user step")
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Processing user input: URL=%s, token length=%s",
                         user_input[CONF_URL],
                         len(user_input[CONF_TOKEN]) if CONF_TOKEN in user_input else 0)
            
            # Validate URL format
            url = user_input[CONF_URL]
            _LOGGER.debug("Validating URL format: %s", url)
            try:
                result = urlparse(url)
                _LOGGER.debug("URL parse result - scheme: %s, netloc: %s, path: %s",
                             result.scheme, result.netloc, result.path)
                
                if not all([result.scheme, result.netloc]):
                    _LOGGER.error("Invalid URL format: %s - missing scheme or netloc", url)
                    errors["base"] = "invalid_url_format"
                else:
                    _LOGGER.debug("URL format is valid, creating client session")
                    session = async_get_clientsession(self.hass)
                    
                    _LOGGER.debug("Initializing Karakeep client with URL: %s", url)
                    client = KarakeepClient(
                        user_input[CONF_URL], user_input[CONF_TOKEN], session
                    )
                    
                    try:
                        _LOGGER.debug("Testing connection to Karakeep API at %s", url)
                        await client.async_get_stats()
                        _LOGGER.info("Successfully connected to Karakeep API")
                        _LOGGER.debug("Creating config entry with title 'Karakeep'")
                        return self.async_create_entry(title="Karakeep", data=user_input)
                    except ClientConnectorError as err:
                        _LOGGER.debug("Connection error details: %s", str(err))
                        _LOGGER.error("Connection error: %s", err)
                        errors["base"] = "cannot_connect"
                    except ClientResponseError as err:
                        _LOGGER.debug(
                            "Response error details - Status: %s, Message: %s, Headers: %s",
                            err.status,
                            err.message,
                            err.headers if hasattr(err, 'headers') else "unknown"
                        )
                        _LOGGER.error("Invalid response from API: %s", err)
                        if err.status == 401:
                            _LOGGER.debug("Authentication error (401) - invalid token")
                            errors["base"] = "invalid_auth"
                        elif err.status == 404:
                            _LOGGER.debug("API path not found (404) - check URL path")
                            errors["base"] = "invalid_api_path"
                        else:
                            _LOGGER.debug("Other API error with status code: %s", err.status)
                            errors["base"] = "api_error"
                    except ClientTimeout as err:
                        _LOGGER.debug("Timeout error details: %s", str(err))
                        _LOGGER.error("Timeout connecting to API")
                        errors["base"] = "timeout_error"
                    except ClientError as err:
                        _LOGGER.debug("Client error type: %s, details: %s", type(err).__name__, str(err))
                        _LOGGER.error("Client error: %s", err)
                        errors["base"] = "client_error"
                    except InvalidURL as err:
                        _LOGGER.debug("Invalid URL error details: %s", str(err))
                        _LOGGER.error("Invalid URL: %s", err)
                        errors["base"] = "invalid_url"
                    except Exception as err:
                        _LOGGER.debug("Unexpected error type: %s", type(err).__name__)
                        _LOGGER.exception("Unexpected error: %s", err)
                        errors["base"] = "unknown"
            except ValueError as err:
                _LOGGER.debug("URL parsing ValueError details: %s", str(err))
                _LOGGER.error("URL parsing error for: %s", url)
                errors["base"] = "invalid_url_format"

        _LOGGER.debug("Creating form schema for config flow")
        schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    cv.positive_int, vol.Range(min=30)
                ),
            }
        )
        
        _LOGGER.debug("Showing form to user with step_id='user', errors=%s", errors)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


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
