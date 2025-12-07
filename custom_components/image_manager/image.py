"""Image platform for the Image Manager integration."""

from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_ENDPOINT, DOMAIN, ENTITY_ID_PATTERN, ENTITY_NAME_PATTERN
from .coordinator import ImageManagerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Image Manager image entities from a config entry."""
    coordinator: ImageManagerCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    # Create entities for existing images
    entities = []
    for image_info in coordinator.data:
        entities.append(ImageManagerImageEntity(coordinator, image_info))

    async_add_entities(entities)

    # Set up listener for coordinator updates (additions and removals)
    @callback
    def _async_update_entities():
        """Update entities based on current coordinator data."""
        current_sequences = {entity.sequence for entity in entities}
        data_sequences = {img["sequence"] for img in coordinator.data}

        # Add new entities
        new_entities = []
        for image_info in coordinator.data:
            sequence = image_info["sequence"]
            if sequence not in current_sequences:
                new_entity = ImageManagerImageEntity(coordinator, image_info)
                new_entities.append(new_entity)
                entities.append(new_entity)

        if new_entities:
            async_add_entities(new_entities)

        # Remove entities that no longer exist
        entities_to_remove = []
        for entity in entities:
            if entity.sequence not in data_sequences:
                entities_to_remove.append(entity)
                entities.remove(entity)

        # Remove from entity registry
        if entities_to_remove:
            registry = er.async_get(hass)
            for entity in entities_to_remove:
                registry.async_remove(entity.entity_id)
                _LOGGER.info("Removed entity %s for deleted image", entity.entity_id)

    # Listen for coordinator updates
    coordinator.async_add_listener(_async_update_entities)


class ImageManagerImageEntity(CoordinatorEntity[ImageManagerCoordinator], ImageEntity):
    """Representation of an Image Manager image entity."""

    @property
    def access_tokens(self) -> list:
        """Return access tokens for compatibility with HA image platform."""
        return ["public"]

    def __init__(
        self,
        coordinator: ImageManagerCoordinator,
        image_info: Dict[str, Any],
    ) -> None:
        """Initialize the image entity."""
        super().__init__(coordinator)
        self._image_info = image_info
        self.sequence = image_info["sequence"]

        # Set entity attributes
        self._attr_unique_id = f"{DOMAIN}_{self.sequence}"
        self._attr_name = ENTITY_NAME_PATTERN.format(sequence=self.sequence)
        self._attr_entity_id = ENTITY_ID_PATTERN.format(sequence=self.sequence)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        # Check if this image still exists in coordinator data
        for image_info in self.coordinator.data:
            if image_info["sequence"] == self.sequence:
                return True
        return False

    @property
    def image_url(self) -> str | None:
        """Return the URL of the image."""
        if not self.available:
            return None

        return f"{API_ENDPOINT}/{self.sequence}"

    @property
    def content_type(self) -> str:
        """Return the content type of the image."""
        return "image/jpeg"

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        """Return extra state attributes."""
        if not self.available:
            return None

        # Find current image info
        current_info = None
        for image_info in self.coordinator.data:
            if image_info["sequence"] == self.sequence:
                current_info = image_info
                break

        if not current_info:
            return None

        return {
            "sequence": current_info["sequence"],
            "filename": current_info["filename"],
            "created_at": current_info["created_at"],
            "size": current_info["size"],
            "width": current_info["width"],
            "height": current_info["height"],
            "timestamp": current_info["timestamp"],
        }

    async def async_image(self) -> bytes | None:
        """Return the image content."""
        if not self.available:
            return None

        try:
            image_path = await self.coordinator.async_get_image_path(self.sequence)
            if not image_path:
                return None

            # Read image file
            import aiofiles

            async with aiofiles.open(image_path, "rb") as f:
                return await f.read()

        except Exception as err:
            _LOGGER.error("Failed to read image %d: %s", self.sequence, err)
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update image info if it still exists
        for image_info in self.coordinator.data:
            if image_info["sequence"] == self.sequence:
                self._image_info = image_info
                break

        self.async_write_ha_state()
