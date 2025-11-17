from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATS = {
    "numBookmarks":  ("Bookmarks", "bookmark", "bookmarks"),
    "numFavorites":  ("Favorites", "star", "favorites"),
    "numArchived":   ("Archived", "archive", "items"),
    "numHighlights": ("Highlights", "marker", "highlights"),
    "numLists":      ("Lists", "format-list-bulleted", "lists"),
    "numTags":       ("Tags", "tag", "tags"),
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Karakeep sensors based on a config entry."""
    _LOGGER.debug("Setting up Karakeep sensor entities for entry_id: %s", entry.entry_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(
        "Retrieved coordinator from hass.data[%s][%s]",
        DOMAIN,
        entry.entry_id,
    )

    entities: list[KarakeepStatSensor] = []
    for key, (name, icon, unit) in STATS.items():
        _LOGGER.debug(
            "Creating KarakeepStatSensor for stat: %s with name: %s",
            key,
            name,
        )
        entities.append(
            KarakeepStatSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                key=key,
                name=name,
                icon=icon,
                unit=unit,
            )
        )

    _LOGGER.debug("Adding %d Karakeep sensor entities", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Karakeep sensor entities setup completed")


class KarakeepStatSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Karakeep statistic as a sensor entity."""

    # Expose as standard sensors (mainly) instead of diagnostics-only
    # Use measurement since these are numeric counts that can change over time.
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry_id: str,
        key: str,
        name: str,
        icon: str,
        unit: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._entry_id = entry_id

        self.entity_description = SensorEntityDescription(
            key=key,
            name=name,
            icon=f"mdi:{icon}",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=unit,
        )

        # Unique per config entry and stat key
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"

        _LOGGER.debug(
            "Initialized KarakeepStatSensor: entry_id=%s key=%s name=%s unique_id=%s",
            entry_id,
            key,
            name,
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
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._key)
        _LOGGER.debug(
            "Getting native value for sensor %s: %s",
            self._attr_unique_id,
            value,
        )
        return value
