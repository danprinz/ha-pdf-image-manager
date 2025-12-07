# Installation Guide - Image Manager Integration

This guide provides detailed instructions for installing and configuring the Image Manager integration for Home Assistant.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
  - [Manual Installation](#manual-installation)
  - [HACS Installation](#hacs-installation)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Verification](#verification)
- [Post-Installation Setup](#post-installation-setup)
- [Troubleshooting Installation](#troubleshooting-installation)

## Prerequisites

Before installing the Image Manager integration, ensure you have:

### System Requirements
- **Home Assistant**: Version 2023.1 or later
- **Python**: 3.10 or later (included with Home Assistant)
- **Storage Space**: At least 1GB free space for image storage
- **Memory**: Minimum 512MB available RAM for image processing

### Dependencies
The integration automatically installs the following Python packages:
- **Pillow >= 8.0.0**: For image processing and validation

### Browser Requirements
For the Lovelace card interface:
- **Chrome**: 60 or later
- **Firefox**: 63 or later
- **Safari**: 12 or later
- **Edge**: 79 or later

## Installation Methods

### Manual Installation

#### Step 1: Download the Integration

1. Download the latest release from the GitHub repository
2. Extract the archive to get the `image_manager` folder

#### Step 2: Copy Files

1. Navigate to your Home Assistant configuration directory:
   ```bash
   cd /config  # or wherever your Home Assistant config is located
   ```

2. Create the custom_components directory if it doesn't exist:
   ```bash
   mkdir -p custom_components
   ```

3. Copy the integration files:
   ```bash
   cp -r image_manager custom_components/
   ```

4. Verify the file structure:
   ```
   config/
   └── custom_components/
       └── image_manager/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── image.py
           ├── image_storage.py
           ├── manifest.json
           ├── services.yaml
           ├── views.py
           ├── translations/
           │   └── en.json
           └── www/
               ├── image-manager-card.js
               └── image-manager-editor.js
   ```

#### Step 3: Set Permissions

Ensure Home Assistant can read the files:
```bash
chown -R homeassistant:homeassistant custom_components/image_manager
chmod -R 755 custom_components/image_manager
```

### HACS Installation

> **Note**: HACS installation is not currently available. Use manual installation instead.

If HACS support is added in the future:

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Image Manager"
5. Click "Install"
6. Restart Home Assistant

## Initial Setup

### Step 1: Restart Home Assistant

After copying the files, restart Home Assistant:

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart Home Assistant**
3. Wait for the system to fully restart (usually 1-2 minutes)

### Step 2: Add Lovelace Resource

**Important**: You must manually add the Lovelace resources before using the cards:

1. Go to **Settings** → **Dashboards** → **Resources**
2. Click the **"Add Resource"** button
3. Add a new resource for each of the following URLs (all are JavaScript Modules):
   - `/hacsfiles/image_manager/image-manager-card.js`
   - `/hacsfiles/image_manager/image-manager-editor.js`
   - `/hacsfiles/image_manager/image-manager-selector-card.js`
   - `/hacsfiles/image_manager/image-manager-selector-editor.js`
4. Click **"Create"** after adding each resource.

### Step 3: Add the Integration

1. Navigate to **Settings** → **Devices & Services**
2. Click **Add Integration** (+ button)
3. Search for "Image Manager"
4. Click on the **Image Manager** integration

### Step 4: Configuration Wizard

The setup wizard will guide you through the configuration:

1. **Name**: Enter a name for your Image Manager instance
   - Default: "Image Manager"
   - This will be used for entity naming

2. **Maximum Images**: Set the storage limit
   - Default: 25 images
   - Range: 1-100 images
   - Consider your available disk space

3. Click **Submit** to complete the setup

## Configuration

### Integration Options

After installation, you can modify settings:

1. Go to **Settings** → **Devices & Services**
2. Find the **Image Manager** integration
3. Click **Configure**

Available options:
- **Name**: Change the integration name
- **Maximum Images**: Adjust storage limit
- **Storage Path**: Custom storage location (advanced)

### Storage Configuration

By default, images are stored in:
```
config/custom_components/image_manager/images/
```

To use a custom storage location:

1. Create the directory:
   ```bash
   mkdir -p /path/to/custom/storage
   chown homeassistant:homeassistant /path/to/custom/storage
   ```

2. Update the configuration through the UI or add to `configuration.yaml`:
   ```yaml
   image_manager:
     storage_path: "/path/to/custom/storage"
   ```

## Verification

### Check Integration Status

1. Go to **Settings** → **Devices & Services**
2. Verify the **Image Manager** integration shows as "Configured"
3. Check for any error messages

### Verify Entities

The integration should create:
- **Configuration entities**: For managing settings
- **Image entities**: Will appear as you upload images (e.g., `image.image_manager_1`)

### Test API Endpoints

Verify the API is working:

1. Open your browser's developer tools
2. Navigate to: `http://your-ha-url:8123/api/image_manager/status`
3. You should see a JSON response with status information

### Check Lovelace Resources

Verify the card resources are loaded:

1. Go to **Settings** → **Dashboards** → **Resources**
2. Look for entries like:
   - `/hacsfiles/image_manager/image-manager-card.js`
   - `/hacsfiles/image_manager/image-manager-editor.js`
   - `/hacsfiles/image_manager/image-manager-selector-card.js`
   - `/hacsfiles/image_manager/image-manager-selector-editor.js`

If missing, add them manually:
```yaml
url: /hacsfiles/image_manager/image-manager-card.js
type: module
```

## Post-Installation Setup

### Add the Lovelace Card

1. Edit a dashboard
2. Click **Add Card**
3. Search for "Image Manager Card"
4. Configure the card options
5. Save the dashboard

### Create Storage Directory

The integration automatically creates the storage directory, but you can verify:

```bash
ls -la config/custom_components/image_manager/images/
```

You should see a `.gitkeep` file indicating the directory exists.

### Set Up Automations (Optional)

Create automations to use the image management services:

```yaml
automation:
  - alias: "Upload Daily Image"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: image_manager.upload_image
        data:
          image_data: "{{ states('sensor.daily_image_b64') }}"
          filename: "daily_{{ now().strftime('%Y%m%d') }}.jpg"
```

## Troubleshooting Installation

### Common Issues

#### Integration Not Found
**Problem**: "Image Manager" doesn't appear in the integration list

**Solutions**:
1. Verify files are in the correct location
2. Check file permissions
3. Restart Home Assistant completely
4. Check Home Assistant logs for errors

#### Permission Errors
**Problem**: Permission denied errors in logs

**Solutions**:
```bash
# Fix ownership
chown -R homeassistant:homeassistant custom_components/image_manager

# Fix permissions
chmod -R 755 custom_components/image_manager
```

#### Dependency Issues
**Problem**: Pillow installation fails

**Solutions**:
1. Check available disk space
2. Manually install Pillow:
   ```bash
   pip install Pillow>=8.0.0
   ```
3. Restart Home Assistant

#### Card Not Loading
**Problem**: Lovelace card doesn't appear

**Solutions**:
1. Clear browser cache (Ctrl+F5)
2. Check browser console for errors
3. Manually add resources to Lovelace
4. Verify file paths are correct

### Log Analysis

Check Home Assistant logs for installation issues:

1. Go to **Settings** → **System** → **Logs**
2. Look for entries containing "image_manager"
3. Common log locations:
   ```
   [custom_components.image_manager] Setup failed
   [homeassistant.loader] Unable to find component image_manager
   ```

### Manual Resource Registration

If automatic resource registration fails, add manually:

1. Go to **Settings** → **Dashboards** → **Resources**
2. Add these resources:

```yaml
# Card resource
url: /hacsfiles/image_manager/image-manager-card.js
type: module

# Editor resource
url: /hacsfiles/image_manager/image-manager-editor.js
type: module

# Selector card resource
url: /hacsfiles/image_manager/image-manager-selector-card.js
type: module

# Selector editor resource
url: /hacsfiles/image_manager/image-manager-selector-editor.js
type: module
```

### Validation Commands

Verify installation with these commands:

```bash
# Check file structure
find config/custom_components/image_manager -type f -name "*.py" | wc -l
# Should return 7

# Check permissions
ls -la config/custom_components/image_manager/
# Should show homeassistant ownership

# Check storage directory
ls -la config/custom_components/image_manager/images/
# Should contain .gitkeep file
```

## Next Steps

After successful installation:

1. **Read the [Usage Guide](USAGE.md)** for detailed usage instructions
2. **Configure your first card** using the Lovelace interface
3. **Upload test images** to verify functionality
4. **Set up automations** to integrate with your smart home
5. **Check the [Troubleshooting Guide](TROUBLESHOOTING.md)** for common issues

## Support

If you encounter issues during installation:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review Home Assistant logs
3. Verify system requirements
4. Check file permissions and ownership
5. Report issues on the GitHub repository

---

**Installation complete!** Your Image Manager integration is ready to use.