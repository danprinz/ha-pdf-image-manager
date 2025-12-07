"""Data update coordinator for the Image Manager integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .image_storage import ImageStorageManager

_LOGGER = logging.getLogger(__name__)


class ImageManagerCoordinator(DataUpdateCoordinator[List[Dict[str, Any]]]):
    """Coordinator to manage image data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        storage_manager: ImageStorageManager,
    ) -> None:
        """Initialize the coordinator."""
        self.storage_manager = storage_manager

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self) -> List[Dict[str, Any]]:
        """Fetch data from the storage manager."""
        try:
            return await self.storage_manager.get_images()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with storage: {err}") from err

    async def async_upload_image(
        self, image_data: bytes, filename: str | None = None
    ) -> Dict[str, Any]:
        """Upload a new image."""
        try:
            image_info = await self.storage_manager.store_image(image_data, filename)
            await self.async_request_refresh()
            return image_info
        except Exception as err:
            _LOGGER.error("Failed to upload image: %s", err)
            raise

    async def async_delete_image(self, sequence: int) -> bool:
        """Delete an image by sequence number."""
        try:
            result = await self.storage_manager.delete_image(sequence)
            if result:
                await self.async_request_refresh()
            return result
        except Exception as err:
            _LOGGER.error("Failed to delete image %d: %s", sequence, err)
            raise

    async def async_delete_all_images(self) -> int:
        """Delete all images."""
        try:
            count = await self.storage_manager.delete_all_images()
            await self.async_request_refresh()
            return count
        except Exception as err:
            _LOGGER.error("Failed to delete all images: %s", err)
            raise

    async def async_get_image_info(self, sequence: int) -> Dict[str, Any] | None:
        """Get image info by sequence number."""
        try:
            return await self.storage_manager.get_image_info(sequence)
        except Exception as err:
            _LOGGER.error("Failed to get image info for %d: %s", sequence, err)
            return None

    async def async_get_image_path(self, sequence: int) -> str | None:
        """Get image file path by sequence number."""
        try:
            path = await self.storage_manager.get_image_path(sequence)
            return str(path) if path else None
        except Exception as err:
            _LOGGER.error("Failed to get image path for %d: %s", sequence, err)
            return None

    async def async_get_pdf_path(self, sequence: int) -> str | None:
        """Get PDF file path by sequence number."""
        try:
            image_info = await self.storage_manager.get_image_info(sequence)
            if image_info and "pdf_filename" in image_info:
                path = self.storage_manager._storage_path / image_info["pdf_filename"]
                return str(path)
            return None
        except Exception as err:
            _LOGGER.error("Failed to get PDF path for %d: %s", sequence, err)
            return None
