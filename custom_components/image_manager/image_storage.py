"""Image storage management for the Image Manager integration."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageOps
import aiofiles

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    IMAGES_DIR,
    METADATA_FILE,
    IMAGE_FILE_PATTERN,
    GITKEEP_FILE,
    REQUIRED_IMAGE_WIDTH,
    REQUIRED_IMAGE_HEIGHT,
    SUPPORTED_FORMATS,
    OUTPUT_FORMAT,
    JPEG_QUALITY,
    MAX_FILE_SIZE,
    ERROR_INVALID_DIMENSIONS,
    ERROR_UNSUPPORTED_FORMAT,
    ERROR_FILE_TOO_LARGE,
)
from .pdf_to_png import pdf_to_png

_LOGGER = logging.getLogger(__name__)


class ImageStorageManager:
    """Manages image storage, validation, and rotation."""

    def __init__(
        self, hass: HomeAssistant, config_entry_id: str, max_images: int = 25
    ) -> None:
        """Initialize the image storage manager."""
        self.hass = hass
        self.config_entry_id = config_entry_id
        self.max_images = max_images
        _LOGGER.info("ImageStorageManager initialized with max_images: %d", max_images)
        self._storage_path = Path(
            hass.config.path("custom_components", "image_manager", IMAGES_DIR)
        )
        self._metadata_path = self._storage_path / METADATA_FILE
        self._lock = asyncio.Lock()

        # Ensure storage directory exists
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Create .gitkeep file if it doesn't exist
        gitkeep_path = self._storage_path / GITKEEP_FILE
        if not gitkeep_path.exists():
            gitkeep_path.touch()

    async def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from storage."""
        if not self._metadata_path.exists():
            return {"images": [], "next_sequence": 1}

        try:
            async with aiofiles.open(self._metadata_path, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, OSError) as err:
            _LOGGER.error("Failed to load metadata: %s", err)
            return {"images": [], "next_sequence": 1}

    async def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to storage."""
        try:
            async with aiofiles.open(self._metadata_path, "w") as f:
                await f.write(json.dumps(metadata, indent=2))
        except OSError as err:
            _LOGGER.error("Failed to save metadata: %s", err)
            raise

    async def validate_image(self, image_data: bytes) -> tuple[bool, str | None]:
        """Validate image data and dimensions."""
        if len(image_data) > MAX_FILE_SIZE:
            return False, ERROR_FILE_TOO_LARGE

        try:
            # Run PIL operations in executor to avoid blocking
            def _validate():
                with Image.open(io.BytesIO(image_data)) as img:
                    # Check format
                    if img.format not in SUPPORTED_FORMATS:
                        return False, ERROR_UNSUPPORTED_FORMAT

                    # Check dimensions
                    if img.size != (REQUIRED_IMAGE_WIDTH, REQUIRED_IMAGE_HEIGHT):
                        return False, ERROR_INVALID_DIMENSIONS

                    return True, None

            import io

            return await self.hass.async_add_executor_job(_validate)

        except Exception as err:
            _LOGGER.error("Failed to validate image: %s", err)
            return False, ERROR_UNSUPPORTED_FORMAT

    async def process_image(self, image_data: bytes) -> bytes:
        """Process image data (convert to JPEG if needed)."""

        def _process():
            import io

            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if needed (for PNG with transparency)
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(
                        img,
                        mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None,
                    )
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Apply EXIF orientation
                img = ImageOps.exif_transpose(img)

                # Save as JPEG
                output = io.BytesIO()
                img.save(
                    output, format=OUTPUT_FORMAT, quality=JPEG_QUALITY, optimize=True
                )
                return output.getvalue()

        return await self.hass.async_add_executor_job(_process)

    def _is_pdf_file(self, file_data: bytes) -> bool:
        """Check if the file data is a PDF file."""
        # PDF files start with %PDF
        return file_data.startswith(b"%PDF")

    async def _convert_pdf_to_png(self, pdf_data: bytes) -> bytes:
        """Convert PDF data to PNG image data."""

        def _convert():
            # Create temporary files for PDF input and PNG output
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_temp:
                pdf_temp.write(pdf_data)
                pdf_temp.flush()

                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as png_temp:
                    try:
                        # Convert PDF to PNG using the pdf_to_png function
                        pdf_to_png(
                            pdf_path=pdf_temp.name,
                            output_path=png_temp.name,
                            target_width=REQUIRED_IMAGE_WIDTH,
                            target_height=REQUIRED_IMAGE_HEIGHT,
                        )

                        # Read the converted PNG data
                        with open(png_temp.name, "rb") as f:
                            png_data = f.read()

                        return png_data

                    finally:
                        # Clean up temporary files
                        try:
                            os.unlink(pdf_temp.name)
                        except OSError:
                            pass
                        try:
                            os.unlink(png_temp.name)
                        except OSError:
                            pass

        return await self.hass.async_add_executor_job(_convert)

    def _generate_filename(
        self,
        sequence: int,
        timestamp: int,
        image_data: bytes,
        filename: Optional[str] = None,
    ) -> str:
        """Generate filename for image."""
        # Create hash of image data
        hash_obj = hashlib.md5(image_data)
        file_hash = hash_obj.hexdigest()[:8]

        return IMAGE_FILE_PATTERN.format(
            sequence=sequence,
            timestamp=timestamp,
            hash=file_hash,
            filename=filename if filename else "image",
        )

    def _generate_pdf_filename(
        self,
        sequence: int,
        timestamp: int,
        pdf_data: bytes,
        filename: Optional[str] = None,
    ) -> str:
        """Generate filename for PDF."""
        # Create hash of PDF data
        hash_obj = hashlib.md5(pdf_data)
        file_hash = hash_obj.hexdigest()[:8]

        return f"image_{sequence}_{timestamp}_{file_hash}_{filename if filename else 'doc'}.pdf"

    async def store_image(
        self, image_data: bytes, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store image with automatic rotation if needed. Converts PDF files to PNG."""
        async with self._lock:
            # Check if the uploaded file is a PDF
            pdf_filename = None
            if self._is_pdf_file(image_data):
                try:
                    _LOGGER.info("PDF file detected, converting to PNG")
                    # Save original PDF data
                    pdf_data = image_data

                    # Convert PDF to PNG
                    image_data = await self._convert_pdf_to_png(image_data)
                    _LOGGER.info("PDF successfully converted to PNG")
                except Exception as err:
                    _LOGGER.error("Failed to convert PDF to PNG: %s", err)
                    raise ValueError(f"Failed to convert PDF to image: {err}")

            # Validate image
            is_valid, error = await self.validate_image(image_data)
            if not is_valid:
                raise ValueError(f"Invalid image: {error}")

            # Process image
            processed_data = await self.process_image(image_data)

            # Load current metadata
            metadata = await self.load_metadata()
            images = metadata["images"]
            next_sequence = metadata["next_sequence"]

            # Generate filename
            timestamp = int(time.time())
            filename = self._generate_filename(
                next_sequence, timestamp, processed_data, filename
            )

            if pdf_filename is None and "pdf_data" in locals():
                pdf_filename = self._generate_pdf_filename(
                    next_sequence, timestamp, pdf_data, filename
                )

            # Check if we need to rotate (remove oldest)
            _LOGGER.info(
                "Current images count: %d, max_images: %d", len(images), self.max_images
            )
            if len(images) >= self.max_images:
                oldest_image = images.pop(0)
                old_path = self._storage_path / oldest_image["filename"]
                try:
                    if old_path.exists():
                        old_path.unlink()
                        _LOGGER.info(
                            "Removed oldest image: %s", oldest_image["filename"]
                        )
                except OSError as err:
                    _LOGGER.warning("Failed to remove old image %s: %s", old_path, err)

                # Remove associated PDF if exists
                if "pdf_filename" in oldest_image and oldest_image["pdf_filename"]:
                    old_pdf_path = self._storage_path / oldest_image["pdf_filename"]
                    try:
                        if old_pdf_path.exists():
                            old_pdf_path.unlink()
                            _LOGGER.info(
                                "Removed oldest PDF: %s", oldest_image["pdf_filename"]
                            )
                    except OSError as err:
                        _LOGGER.warning(
                            "Failed to remove old PDF %s: %s", old_pdf_path, err
                        )

            # Save new image
            file_path = self._storage_path / filename
            try:
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(processed_data)
            except OSError as err:
                _LOGGER.error("Failed to save image %s: %s", filename, err)
                raise

            # Save PDF if exists
            if pdf_filename:
                pdf_path = self._storage_path / pdf_filename
                try:
                    async with aiofiles.open(pdf_path, "wb") as f:
                        await f.write(pdf_data)
                except OSError as err:
                    _LOGGER.error("Failed to save PDF %s: %s", pdf_filename, err)
                    # Try to cleanup image file
                    try:
                        file_path.unlink()
                    except OSError:
                        pass
                    raise

            # Create image metadata
            image_info = {
                "sequence": next_sequence,
                "filename": filename,
                "timestamp": timestamp,
                "created_at": dt_util.utcnow().isoformat(),
                "size": len(processed_data),
                "width": REQUIRED_IMAGE_WIDTH,
                "height": REQUIRED_IMAGE_HEIGHT,
            }

            if pdf_filename:
                image_info["pdf_filename"] = pdf_filename

            # Add to metadata
            images.append(image_info)
            metadata["images"] = images
            metadata["next_sequence"] = next_sequence + 1

            # Save metadata
            await self.save_metadata(metadata)

            _LOGGER.info("Stored image: %s (sequence: %d)", filename, next_sequence)
            return image_info

    async def delete_image(self, sequence: int) -> bool:
        """Delete image by sequence number."""
        async with self._lock:
            metadata = await self.load_metadata()
            images = metadata["images"]

            # Find image by sequence
            image_to_delete = None
            for i, img in enumerate(images):
                if img["sequence"] == sequence:
                    image_to_delete = images.pop(i)
                    break

            if not image_to_delete:
                return False

            # Delete file
            file_path = self._storage_path / image_to_delete["filename"]
            try:
                if file_path.exists():
                    file_path.unlink()
                    _LOGGER.info("Deleted image: %s", image_to_delete["filename"])
            except OSError as err:
                _LOGGER.warning("Failed to delete image file %s: %s", file_path, err)

            # Delete PDF file if exists
            if "pdf_filename" in image_to_delete and image_to_delete["pdf_filename"]:
                pdf_path = self._storage_path / image_to_delete["pdf_filename"]
                try:
                    if pdf_path.exists():
                        pdf_path.unlink()
                        _LOGGER.info("Deleted PDF: %s", image_to_delete["pdf_filename"])
                except OSError as err:
                    _LOGGER.warning("Failed to delete PDF file %s: %s", pdf_path, err)

            # Save updated metadata
            await self.save_metadata(metadata)
            return True

    async def delete_all_images(self) -> int:
        """Delete all stored images."""
        async with self._lock:
            metadata = await self.load_metadata()
            images = metadata["images"]
            deleted_count = 0

            # Delete all image files
            for img in images:
                file_path = self._storage_path / img["filename"]
                try:
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                        _LOGGER.info("Deleted image: %s", img["filename"])
                except OSError as err:
                    _LOGGER.warning(
                        "Failed to delete image file %s: %s", file_path, err
                    )

                # Delete PDF file if exists
                if "pdf_filename" in img and img["pdf_filename"]:
                    pdf_path = self._storage_path / img["pdf_filename"]
                    try:
                        if pdf_path.exists():
                            pdf_path.unlink()
                            _LOGGER.info("Deleted PDF: %s", img["pdf_filename"])
                    except OSError as err:
                        _LOGGER.warning(
                            "Failed to delete PDF file %s: %s", pdf_path, err
                        )

            # Reset metadata
            metadata = {"images": [], "next_sequence": 1}
            await self.save_metadata(metadata)

            _LOGGER.info("Deleted %d images", deleted_count)
            return deleted_count

    async def get_images(self) -> List[Dict[str, Any]]:
        """Get list of all stored images."""
        metadata = await self.load_metadata()
        return metadata["images"]

    async def get_image_path(self, sequence: int) -> Optional[Path]:
        """Get file path for image by sequence number."""
        metadata = await self.load_metadata()
        for img in metadata["images"]:
            if img["sequence"] == sequence:
                return self._storage_path / img["filename"]
        return None

    async def get_image_info(self, sequence: int) -> Optional[Dict[str, Any]]:
        """Get image info by sequence number."""
        metadata = await self.load_metadata()
        for img in metadata["images"]:
            if img["sequence"] == sequence:
                return img
        return None
