from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_URL, CONF_TOKEN
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, CONF_SCAN_INTERVAL, PLATFORMS
from .api import KarakeepClient

_LOGGER = logging.getLogger(__name__)

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
    _LOGGER.debug("Creating Karakeep client with timeout: %s seconds", scan_interval)
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
            
            return data
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
