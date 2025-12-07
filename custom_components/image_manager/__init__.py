"""The Image Manager integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_MAX_IMAGES,
    DEFAULT_MAX_IMAGES,
    SERVICE_UPLOAD_IMAGE,
    SERVICE_DELETE_IMAGE,
    SERVICE_DELETE_ALL_IMAGES,
    ATTR_IMAGE_DATA,
    ATTR_FILENAME,
    ATTR_SEQUENCE,
    API_ENDPOINT,
)
from .coordinator import ImageManagerCoordinator
from .image_storage import ImageStorageManager
from .views import (
    ImageManagerView,
    ImageManagerPdfView,
    ImageManagerStatusView,
    ImageManagerUploadView,
    ImageManagerDeleteView,
    ImageManagerClearAllView,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.IMAGE]

# Service schemas
SERVICE_UPLOAD_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMAGE_DATA): str,  # Base64 encoded image data
        vol.Optional(ATTR_FILENAME): str,
    }
)

SERVICE_DELETE_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SEQUENCE): int,
    }
)

SERVICE_DELETE_ALL_IMAGES_SCHEMA = vol.Schema({})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Image Manager integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Image Manager from a config entry."""
    max_images = entry.options.get(
        CONF_MAX_IMAGES, entry.data.get(CONF_MAX_IMAGES, DEFAULT_MAX_IMAGES)
    )
    _LOGGER.info(
        "Setting up Image Manager with max_images: %s (from config entry data: %s, options: %s)",
        max_images,
        entry.data,
        entry.options,
    )

    # Initialize storage manager
    storage_manager = ImageStorageManager(hass, entry.entry_id, max_images)

    # Initialize coordinator
    coordinator = ImageManagerCoordinator(hass, storage_manager)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Clean up excess images if max_images was reduced
    images = await storage_manager.get_images()
    if len(images) > max_images:
        excess_count = len(images) - max_images
        _LOGGER.info(
            "Cleaning up %d excess images (max_images reduced to %d)",
            excess_count,
            max_images,
        )
        for _ in range(excess_count):
            oldest_image = images.pop(0)
            try:
                file_path = await storage_manager.get_image_path(
                    oldest_image["sequence"]
                )
                if file_path and file_path.exists():
                    file_path.unlink()
                    _LOGGER.info("Removed excess image: %s", oldest_image["filename"])
            except (OSError, Exception) as err:
                _LOGGER.warning(
                    "Failed to remove excess image %s: %s",
                    oldest_image["filename"],
                    err,
                )

        # Update metadata
        metadata = await storage_manager.load_metadata()
        metadata["images"] = images
        await storage_manager.save_metadata(metadata)
        _LOGGER.info("Cleaned up %d excess images", excess_count)

    # Store coordinator in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "storage_manager": storage_manager,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register API views
    hass.http.register_view(ImageManagerView(coordinator))
    hass.http.register_view(ImageManagerPdfView(coordinator))
    hass.http.register_view(ImageManagerStatusView(coordinator))
    hass.http.register_view(ImageManagerUploadView(coordinator))
    hass.http.register_view(ImageManagerDeleteView(coordinator))
    hass.http.register_view(ImageManagerClearAllView(coordinator))

    # Register frontend resources
    try:
        from homeassistant.components.http import StaticPathConfig

        # Register static path for frontend resources
        www_path = hass.config.path("custom_components/image_manager/www")
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/hacsfiles/image_manager", www_path, cache_headers=False
                )
            ]
        )

    except ImportError:
        # Fallback for older HA versions
        hass.http.register_static_path(
            "/hacsfiles/image_manager",
            hass.config.path("custom_components/image_manager/www"),
            cache_headers=False,
        )

    # Note: Lovelace resources must be manually added by users
    # Add this to your Lovelace resources:
    # - url: /hacsfiles/image_manager/image-manager.js
    #   type: module
    _LOGGER.info(
        "Image Manager frontend resources are available at /hacsfiles/image_manager/. "
        "Please add the card manually to your Lovelace resources if needed."
    )

    # Register services
    await _async_register_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_register_services(
    hass: HomeAssistant, coordinator: ImageManagerCoordinator
) -> None:
    """Register services for the integration."""

    async def async_upload_image(call: ServiceCall) -> None:
        """Handle upload image service call."""
        import base64

        try:
            # Decode base64 image data
            image_data_b64 = call.data[ATTR_IMAGE_DATA]
            image_data = base64.b64decode(image_data_b64)
            filename = call.data.get(ATTR_FILENAME)

            # Upload image
            image_info = await coordinator.async_upload_image(image_data, filename)

            _LOGGER.info(
                "Image uploaded successfully: sequence %d", image_info["sequence"]
            )

        except Exception as err:
            _LOGGER.error("Failed to upload image: %s", err)
            raise

    async def async_delete_image(call: ServiceCall) -> None:
        """Handle delete image service call."""
        try:
            sequence = call.data[ATTR_SEQUENCE]
            success = await coordinator.async_delete_image(sequence)

            if success:
                _LOGGER.info("Image deleted successfully: sequence %d", sequence)
            else:
                _LOGGER.warning("Image not found: sequence %d", sequence)

        except Exception as err:
            _LOGGER.error("Failed to delete image: %s", err)
            raise

    async def async_delete_all_images(call: ServiceCall) -> None:
        """Handle delete all images service call."""
        try:
            count = await coordinator.async_delete_all_images()
            _LOGGER.info("Deleted %d images", count)

        except Exception as err:
            _LOGGER.error("Failed to delete all images: %s", err)
            raise

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPLOAD_IMAGE,
        async_upload_image,
        schema=SERVICE_UPLOAD_IMAGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_IMAGE,
        async_delete_image,
        schema=SERVICE_DELETE_IMAGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_ALL_IMAGES,
        async_delete_all_images,
        schema=SERVICE_DELETE_ALL_IMAGES_SCHEMA,
    )
