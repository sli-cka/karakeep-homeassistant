from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from aiohttp import (
    ClientResponseError,
    ClientTimeout,
    ClientConnectorError,
    ServerTimeoutError,
    ClientError,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import issue_registry as ir
from homeassistant.const import CONF_URL, CONF_TOKEN
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, CONF_SCAN_INTERVAL, PLATFORMS, CONF_ENABLE_UPDATES, DEFAULT_ENABLE_UPDATES
from .api import KarakeepClient

_LOGGER = logging.getLogger(__name__)

ISSUE_API_UNAVAILABLE = "api_unavailable"

# Connection-related exceptions that indicate API unavailability
CONNECTION_EXCEPTIONS = (
    ClientConnectorError,
    ServerTimeoutError,
    asyncio.TimeoutError,
    TimeoutError,
    ConnectionError,
    OSError,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Karakeep from a config entry."""
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    _LOGGER.debug(
        "Setting up Karakeep integration for entry_id: %s with URL: %s",
        entry.entry_id,
        entry.data[CONF_URL]
    )
    
    session = async_get_clientsession(hass)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    enable_updates = entry.options.get(
        CONF_ENABLE_UPDATES,
        entry.data.get(CONF_ENABLE_UPDATES, DEFAULT_ENABLE_UPDATES)
    )
    _LOGGER.debug(
        "Creating Karakeep client with timeout: %s seconds, enable_updates: %s",
        scan_interval,
        enable_updates,
    )
    client = KarakeepClient(entry.data[CONF_URL], entry.data[CONF_TOKEN], session)

    async def async_update_data():
        """Fetch data from Karakeep API."""
        _LOGGER.debug("Starting data update from Karakeep API")
        try:
            # Fetch stats
            data = await client.async_get_stats()
            _LOGGER.debug("Stats update successful, received %d data points", len(data) if data else 0)
            
            # Fetch health status
            health_data = await client.async_get_health()
            data["health"] = health_data
            _LOGGER.debug("Health check successful: %s", health_data)

            # Fetch version
            version = await client.async_get_version()
            data["version"] = version
            _LOGGER.debug("Version check successful: %s", version)

            # Fetch latest version from GitHub (only if enabled)
            if enable_updates:
                try:
                    async with session.get(
                        "https://api.github.com/repos/karakeep-app/karakeep/releases/latest",
                        timeout=ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            gh_data = await resp.json()
                            data["latest_version"] = gh_data.get("tag_name", "").lstrip("v")
                            data["release_url"] = gh_data.get("html_url")
                            data["release_notes"] = gh_data.get("body")
                            _LOGGER.debug("Latest version check successful: %s", data["latest_version"])
                        else:
                            _LOGGER.warning("Failed to fetch latest version from GitHub: %s", resp.status)
                except Exception as err:
                    _LOGGER.warning("Error fetching latest version from GitHub: %s", err)
            else:
                _LOGGER.debug("Update entity disabled, skipping GitHub version check")
            
            # API is available, delete any existing repair issue
            ir.async_delete_issue(hass, DOMAIN, f"{ISSUE_API_UNAVAILABLE}_{entry.entry_id}")
            
            return data
        except ClientResponseError as err:
            if err.status == 401:
                _LOGGER.error(
                    "Authentication failed for Karakeep API. Token may be invalid or expired."
                )
                raise ConfigEntryAuthFailed(
                    "Invalid or expired API token. Please reauthenticate."
                ) from err
            _LOGGER.debug("Data update failed with response error: %s", str(err))
            raise UpdateFailed(f"API error: {err}") from err
        except CONNECTION_EXCEPTIONS as err:
            _LOGGER.error(
                "Karakeep API at %s is unavailable: %s",
                entry.data[CONF_URL],
                str(err)
            )
            # Create a repair issue for API unavailability
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"{ISSUE_API_UNAVAILABLE}_{entry.entry_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_API_UNAVAILABLE,
                translation_placeholders={
                    "url": entry.data[CONF_URL],
                    "error": str(err),
                },
            )
            raise UpdateFailed(f"API unavailable: {err}") from err
        except Exception as err:
            _LOGGER.debug("Data update failed: %s", str(err))
            raise UpdateFailed(err) from err
    _LOGGER.debug(
        "Creating DataUpdateCoordinator with update interval: %s seconds",
        scan_interval
    )
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=scan_interval),
        update_method=async_update_data,
        config_entry=entry
    )

    _LOGGER.debug("Performing initial data refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial data refresh completed")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _LOGGER.debug("Stored coordinator in hass.data[%s][%s]", DOMAIN, entry.entry_id)

    _LOGGER.debug("Setting up platform entities: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Karakeep integration setup completed successfully")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Karakeep entry."""
    _LOGGER.debug("Unloading Karakeep integration for entry_id: %s", entry.entry_id)

    # Clean up any repair issues created by this entry
    ir.async_delete_issue(hass, DOMAIN, f"{ISSUE_API_UNAVAILABLE}_{entry.entry_id}")

    _LOGGER.debug("Unloading platforms: %s", PLATFORMS)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        _LOGGER.debug("Successfully unloaded platforms, removing entry data")
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Karakeep integration unloaded successfully")
    else:
        _LOGGER.warning("Failed to unload all platforms for Karakeep integration")
        
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
