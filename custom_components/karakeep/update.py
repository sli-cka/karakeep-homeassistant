from __future__ import annotations

import logging

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_ENABLE_UPDATES, DEFAULT_ENABLE_UPDATES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Karakeep update entity based on a config entry."""
    enable_updates = entry.options.get(
        CONF_ENABLE_UPDATES,
        entry.data.get(CONF_ENABLE_UPDATES, DEFAULT_ENABLE_UPDATES)
    )

    unique_id = f"{entry.entry_id}_update"

    if not enable_updates:
        _LOGGER.debug("Update entity disabled for entry_id: %s, removing if exists", entry.entry_id)
        # Remove the entity from the registry if it was previously created
        ent_reg = er.async_get(hass)
        entity_id = ent_reg.async_get_entity_id("update", DOMAIN, unique_id)
        if entity_id:
            _LOGGER.debug("Removing update entity: %s", entity_id)
            ent_reg.async_remove(entity_id)
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KarakeepUpdateEntity(coordinator, entry)])


class KarakeepUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Defines a Karakeep update entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_entity_category = EntityCategory.CONFIG

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