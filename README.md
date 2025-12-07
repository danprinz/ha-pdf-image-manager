# Image Manager

This integration allows you to manage images in Home Assistant, including uploading, converting (PDF to Image), and deleting.

## Installation

### HACS

1. Open HACS.
2. Go to "Integrations".
3. Click the 3 dots in the top right corner and select "Custom repositories".
4. Add the URL of this repository.
5. Select "Integration" as the category.
6. Click "Add".
7. Find "Image Manager" in the list and install it.
8. Restart Home Assistant.

### Manual

1. Copy the `custom_components/image_manager` folder to your `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

This integration supports config flow. Go to Settings -> Devices & Services -> Add Integration and search for "Image Manager".

## Frontend Card

To use the image manager selector card in your dashboard:

1. Go to Settings -> Dashboards -> 3 dots (top right) -> Resources.
2. Add Resource:
   - URL: `/hacsfiles/image_manager/image-manager.js`
   - Type: JavaScript Module
3. Refresh your dashboard.

This resource contains both the `image-manager-card` (management interface) and `image-manager-selector-card` (dropdown selector).

