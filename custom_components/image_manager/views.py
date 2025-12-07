"""Views for serving images from the Image Manager integration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import (
    API_ENDPOINT,
    REQUIRED_IMAGE_WIDTH,
    REQUIRED_IMAGE_HEIGHT,
    MAX_FILE_SIZE,
)
from .coordinator import ImageManagerCoordinator

_LOGGER = logging.getLogger(__name__)


class ImageManagerView(HomeAssistantView):
    """View to serve images from the Image Manager."""

    url = f"{API_ENDPOINT}/{{sequence}}"
    name = "api:image_manager:images"
    requires_auth = False  # Images are served publicly

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def get(self, request: web.Request, sequence: str) -> web.Response:
        """Serve an image by sequence number."""
        try:
            sequence_int = int(sequence)
        except ValueError:
            raise HTTPNotFound() from None

        # Get image path
        image_path = await self.coordinator.async_get_image_path(sequence_int)
        if not image_path:
            raise HTTPNotFound()

        # Check if file exists
        path_obj = Path(image_path)
        if not path_obj.exists():
            _LOGGER.warning("Image file not found: %s", image_path)
            raise HTTPNotFound()

        # Serve the file
        try:
            return web.FileResponse(
                path=image_path,
                headers={
                    "Content-Type": "image/jpeg",
                    "Cache-Control": "public, max-age=3600",
                },
            )
        except Exception as err:
            _LOGGER.error("Failed to serve image %s: %s", image_path, err)
            raise HTTPNotFound() from err


class ImageManagerPdfView(HomeAssistantView):
    """View to serve PDFs from the Image Manager."""

    url = f"{API_ENDPOINT}/{{sequence}}/pdf"
    name = "api:image_manager:pdfs"
    requires_auth = False  # PDFs are served publicly (like images)

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def get(self, request: web.Request, sequence: str) -> web.Response:
        """Serve a PDF by sequence number."""
        try:
            sequence_int = int(sequence)
        except ValueError:
            raise HTTPNotFound() from None

        # Get PDF path
        pdf_path = await self.coordinator.async_get_pdf_path(sequence_int)
        if not pdf_path:
            raise HTTPNotFound()

        # Check if file exists
        path_obj = Path(pdf_path)
        if not path_obj.exists():
            _LOGGER.warning("PDF file not found: %s", pdf_path)
            raise HTTPNotFound()

        # Serve the file
        try:
            return web.FileResponse(
                path=pdf_path,
                headers={
                    "Content-Type": "application/pdf",
                    "Cache-Control": "public, max-age=3600",
                },
            )
        except Exception as err:
            _LOGGER.error("Failed to serve PDF %s: %s", pdf_path, err)
            raise HTTPNotFound() from err


class ImageManagerAPIView(HomeAssistantView):
    """API view for image manager operations."""

    url = "/api/image_manager"
    name = "api:image_manager"
    requires_auth = True

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def get(self, request: web.Request) -> web.Response:
        """Get status and list of images."""
        path = request.path_qs.split("/")[-1]

        if path == "status":
            return await self._handle_status(request)

        return web.Response(status=404)

    async def post(self, request: web.Request) -> web.Response:
        """Handle POST requests for upload, delete, and clear operations."""
        path = request.path_qs.split("/")[-1]

        if path == "upload":
            return await self._handle_upload(request)
        elif path == "delete":
            return await self._handle_delete(request)
        elif path == "clear_all":
            return await self._handle_clear_all(request)

        return web.Response(status=404)

    async def _handle_status(self, request: web.Request) -> web.Response:
        """Handle status request."""
        try:
            images = self.coordinator.data or []
            max_images = self.coordinator.storage_manager.max_images

            status_data = {
                "images": [
                    {
                        "sequence": img["sequence"],
                        "filename": img.get("filename", f"image_{img['sequence']}"),
                        "timestamp": img["timestamp"],
                        "url": f"{API_ENDPOINT}/{img['sequence']}",
                        "entity_id": f"image.image_manager_{img['sequence']}",
                    }
                    for img in images
                ],
                "count": len(images),
                "max_images": max_images,
                "storage_full": len(images) >= max_images,
            }

            return web.json_response(status_data)
        except Exception as err:
            _LOGGER.error("Failed to get status: %s", err)
            return web.json_response({"error": str(err)}, status=500)

    async def _handle_upload(self, request: web.Request) -> web.Response:
        """Handle image upload."""
        try:
            # Check content type
            if not request.content_type.startswith("multipart/form-data"):
                return web.json_response(
                    {"error": "Content-Type must be multipart/form-data"}, status=400
                )

            # Read multipart data
            reader = await request.multipart()
            image_data = None
            filename = None

            async for field in reader:
                if field.name == "image":
                    image_data = await field.read()
                    filename = field.filename
                elif field.name == "filename":
                    filename = await field.text()

            if not image_data:
                return web.json_response(
                    {"error": "No image data provided"}, status=400
                )

            # Check file size
            if len(image_data) > MAX_FILE_SIZE:
                return web.json_response(
                    {
                        "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
                    },
                    status=400,
                )

            # Upload image
            image_info = await self.coordinator.async_upload_image(image_data, filename)

            return web.json_response(
                {
                    "success": True,
                    "image": {
                        "sequence": image_info["sequence"],
                        "filename": image_info.get(
                            "filename", f"image_{image_info['sequence']}"
                        ),
                        "timestamp": image_info["timestamp"],
                        "url": f"{API_ENDPOINT}/{image_info['sequence']}",
                        "entity_id": f"image.image_manager_{image_info['sequence']}",
                    },
                }
            )

        except Exception as err:
            _LOGGER.error("Failed to upload image: %s", err)
            return web.json_response({"error": str(err)}, status=500)

    async def _handle_delete(self, request: web.Request) -> web.Response:
        """Handle image deletion."""
        try:
            data = await request.json()
            sequence = data.get("sequence")

            if sequence is None:
                return web.json_response(
                    {"error": "Sequence number required"}, status=400
                )

            success = await self.coordinator.async_delete_image(sequence)

            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"error": "Image not found"}, status=404)

        except Exception as err:
            _LOGGER.error("Failed to delete image: %s", err)
            return web.json_response({"error": str(err)}, status=500)

    async def _handle_clear_all(self, request: web.Request) -> web.Response:
        """Handle clear all images."""
        try:
            count = await self.coordinator.async_delete_all_images()
            return web.json_response({"success": True, "deleted_count": count})

        except Exception as err:
            _LOGGER.error("Failed to clear all images: %s", err)
            return web.json_response({"error": str(err)}, status=500)


class ImageManagerStatusView(HomeAssistantView):
    """Status endpoint for image manager."""

    url = "/api/image_manager/status"
    name = "api:image_manager:status"
    requires_auth = True

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def get(self, request: web.Request) -> web.Response:
        """Get status and list of images."""
        try:
            images = self.coordinator.data or []
            max_images = self.coordinator.storage_manager.max_images

            status_data = {
                "images": [
                    {
                        "sequence": img["sequence"],
                        "filename": img.get("filename", f"image_{img['sequence']}"),
                        "timestamp": img["timestamp"],
                        "url": f"{API_ENDPOINT}/{img['sequence']}",
                        "pdf_url": f"{API_ENDPOINT}/{img['sequence']}/pdf"
                        if img.get("pdf_filename")
                        else None,
                        "entity_id": f"image.image_manager_{img['sequence']}",
                    }
                    for img in images
                ],
                "count": len(images),
                "max_images": max_images,
                "storage_full": False,  # Always allow uploads, auto-rotation handles capacity
            }

            return web.json_response(status_data)
        except Exception as err:
            _LOGGER.error("Failed to get status: %s", err)
            return web.json_response({"error": str(err)}, status=500)


class ImageManagerUploadView(HomeAssistantView):
    """Upload endpoint for image manager."""

    url = "/api/image_manager/upload"
    name = "api:image_manager:upload"
    requires_auth = True

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        """Handle image upload."""
        try:
            # Check content type
            if not request.content_type.startswith("multipart/form-data"):
                return web.json_response(
                    {"error": "Content-Type must be multipart/form-data"}, status=400
                )

            # Read multipart data
            reader = await request.multipart()
            image_data = None
            filename = None

            async for field in reader:
                if field.name == "image":
                    image_data = await field.read()
                    filename = field.filename
                elif field.name == "filename":
                    filename = await field.text()

            if not image_data:
                return web.json_response(
                    {"error": "No image data provided"}, status=400
                )

            # Check file size
            if len(image_data) > MAX_FILE_SIZE:
                return web.json_response(
                    {
                        "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
                    },
                    status=400,
                )

            # Upload image
            image_info = await self.coordinator.async_upload_image(image_data, filename)

            return web.json_response(
                {
                    "success": True,
                    "image": {
                        "sequence": image_info["sequence"],
                        "filename": image_info.get(
                            "filename", f"image_{image_info['sequence']}"
                        ),
                        "timestamp": image_info["timestamp"],
                        "url": f"{API_ENDPOINT}/{image_info['sequence']}",
                        "entity_id": f"image.image_manager_{image_info['sequence']}",
                    },
                }
            )

        except Exception as err:
            _LOGGER.error("Failed to upload image: %s", err)
            return web.json_response({"error": str(err)}, status=500)


class ImageManagerDeleteView(HomeAssistantView):
    """Delete endpoint for image manager."""

    url = "/api/image_manager/delete"
    name = "api:image_manager:delete"
    requires_auth = True

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        """Handle image deletion."""
        try:
            data = await request.json()
            sequence = data.get("sequence")

            if sequence is None:
                return web.json_response(
                    {"error": "Sequence number required"}, status=400
                )

            success = await self.coordinator.async_delete_image(sequence)

            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"error": "Image not found"}, status=404)

        except Exception as err:
            _LOGGER.error("Failed to delete image: %s", err)
            return web.json_response({"error": str(err)}, status=500)


class ImageManagerClearAllView(HomeAssistantView):
    """Clear all endpoint for image manager."""

    url = "/api/image_manager/clear_all"
    name = "api:image_manager:clear_all"
    requires_auth = True

    def __init__(self, coordinator: ImageManagerCoordinator) -> None:
        """Initialize the view."""
        self.coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        """Handle clear all images."""
        try:
            count = await self.coordinator.async_delete_all_images()
            return web.json_response({"success": True, "deleted_count": count})

        except Exception as err:
            _LOGGER.error("Failed to clear all images: %s", err)
            return web.json_response({"error": str(err)}, status=500)
