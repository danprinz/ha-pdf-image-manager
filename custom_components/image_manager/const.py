"""Constants for the Image Manager integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "image_manager"

# Configuration keys
CONF_NAME: Final = "name"
CONF_MAX_IMAGES: Final = "max_images"

# Default values
DEFAULT_NAME: Final = "Image Manager"
DEFAULT_MAX_IMAGES: Final = 25
MAX_IMAGE_WIDTH: Final = 3840
MAX_IMAGE_HEIGHT: Final = 2160
REQUIRED_IMAGE_WIDTH: Final = 3840
REQUIRED_IMAGE_HEIGHT: Final = 2160

# File paths and naming
IMAGES_DIR: Final = "images"
METADATA_FILE: Final = "metadata.json"
IMAGE_FILE_PATTERN: Final = "img_{sequence:03d}_{timestamp}_{hash}_{filename}.png"
GITKEEP_FILE: Final = ".gitkeep"

# Supported formats
SUPPORTED_FORMATS: Final = ["JPEG", "PNG"]
OUTPUT_FORMAT: Final = "PNG"
JPEG_QUALITY: Final = 100

# Entity configuration
ENTITY_ID_PATTERN: Final = "image.image_manager_{sequence}"
ENTITY_NAME_PATTERN: Final = "Image Manager {sequence}"

# Services
SERVICE_UPLOAD_IMAGE: Final = "upload_image"
SERVICE_DELETE_IMAGE: Final = "delete_image"
SERVICE_DELETE_ALL_IMAGES: Final = "delete_all_images"

# Service data keys
ATTR_IMAGE_DATA: Final = "image_data"
ATTR_FILENAME: Final = "filename"
ATTR_SEQUENCE: Final = "sequence"

# API endpoints
API_ENDPOINT: Final = "/image_manager/images"

# Error messages
ERROR_INVALID_DIMENSIONS: Final = "invalid_dimensions"
ERROR_UNSUPPORTED_FORMAT: Final = "unsupported_format"
ERROR_FILE_TOO_LARGE: Final = "file_too_large"
ERROR_STORAGE_FULL: Final = "storage_full"
ERROR_IMAGE_NOT_FOUND: Final = "image_not_found"

# File size limits (in bytes)
MAX_FILE_SIZE: Final = 50 * 1024 * 1024  # 50MB