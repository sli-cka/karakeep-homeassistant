from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Karakeep binary sensors based on a config entry."""
    _LOGGER.debug("Setting up Karakeep binary sensor entities for entry_id: %s", entry.entry_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(
        "Retrieved coordinator from hass.data[%s][%s]",
        DOMAIN,
        entry.entry_id,
    )

    entities = [
        KarakeepHealthSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
        )
    ]

    _LOGGER.debug("Adding %d Karakeep binary sensor entities", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Karakeep binary sensor entities setup completed")


class KarakeepHealthSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of Karakeep health status as a binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = "Health"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_health"

        _LOGGER.debug(
            "Initialized KarakeepHealthSensor: entry_id=%s unique_id=%s",
            entry_id,
            self._attr_unique_id,
        )

    @property
    def device_info(self) -> dict:
        """Return device info to group entities under a service."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Karakeep",
            "manufacturer": "Karakeep",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def is_on(self) -> bool:
        """Return true if the health check indicates a problem."""
        health_data = self.coordinator.data.get("health", {})
        status_code = health_data.get("status_code", 0)
        status = health_data.get("status", "unknown")
        
        _LOGGER.debug(
            "Health check for sensor %s: status_code=%s, status=%s",
            self._attr_unique_id,
            status_code,
            status,
        )
        
        # Return True if there's a problem (not 200 OK)
        # Binary sensor with PROBLEM class: True = problem detected, False = no problem
        is_problem = status_code != 200 or status.lower() != "ok"
        
        _LOGGER.debug(
            "Health sensor %s problem state: %s",
            self._attr_unique_id,
            is_problem,
        )
        
        return is_problem

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success