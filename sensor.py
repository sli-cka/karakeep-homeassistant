from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATS = {
    "numBookmarks":  ("Bookmarks", "bookmark"),
    "numFavorites":  ("Favorites", "star"),
    "numArchived":   ("Archived", "archive"),
    "numHighlights": ("Highlights", "marker"),
    "numLists":      ("Lists", "format-list-bulleted"),
    "numTags":       ("Tags", "tag"),
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Karakeep sensors based on a config entry."""
    _LOGGER.debug("Setting up Karakeep sensor entities for entry_id: %s", entry.entry_id)
    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Retrieved coordinator from hass.data[%s][%s]", DOMAIN, entry.entry_id)
    
    entities = []
    for key, val in STATS.items():
        _LOGGER.debug("Creating sensor entity for stat: %s with name: %s", key, val[0])
        entities.append(KarakeepStatSensor(coordinator, key, *val))
    
    _LOGGER.debug("Adding %d sensor entities to Home Assistant", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Karakeep sensor entities setup completed")

class KarakeepStatSensor(CoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key, name, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self.entity_description = SensorEntityDescription(
            key=key,
            name=f"Karakeep {name}",
            icon=f"mdi:{icon}",
            state_class=SensorStateClass.MEASUREMENT,
        )
        self._attr_unique_id = f"karakeep_{key}"
        _LOGGER.debug(
            "Initialized KarakeepStatSensor: key=%s, name='Karakeep %s', unique_id=%s",
            key, name, self._attr_unique_id
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._key)
        _LOGGER.debug(
            "Getting native value for sensor %s: %s",
            self._attr_unique_id, value
        )
        return value
