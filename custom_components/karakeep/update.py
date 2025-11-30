from __future__ import annotations

import logging

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up Karakeep update entity based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([KarakeepUpdateEntity(coordinator, entry)])


class KarakeepUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Defines a Karakeep update entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_update"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Karakeep",
            "manufacturer": "Karakeep",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def installed_version(self) -> str | None:
        """Return the current app version."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("version")

    @property
    def latest_version(self) -> str | None:
        """Return the latest available version."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("latest_version")

    @property
    def release_url(self) -> str | None:
        """Return the release URL."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("release_url")

    async def async_release_notes(self) -> str | None:
        """Return the release notes."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("release_notes")