# Image Manager for Home Assistant

A comprehensive Home Assistant integration for managing 4K images with a user-friendly Lovelace card interface. Perfect for storing and managing high-resolution images for use in dashboards, automations, and picture-element cards.

## 🌟 Features

### 📤 Image Upload & Management
- **Drag & Drop Interface**: Intuitive web-based upload through custom Lovelace card
- **4K Image Support**: Optimized for 3840×2160 pixel images
- **Format Support**: JPEG and PNG input with JPEG output optimization
- **Storage Management**: Up to 25 images with intelligent storage tracking
- **Bulk Operations**: Upload multiple images or clear all at once

### 🎯 Home Assistant Integration
- **Entity Creation**: Each image becomes a `image.image_manager_X` entity
- **Service Calls**: Upload, delete, and manage images via services
- **API Endpoints**: RESTful API for external integrations
- **Config Flow**: Easy setup through Home Assistant UI
- **Lovelace Card**: Custom card with visual management interface

### 🔧 Advanced Features
- **Image Validation**: Automatic dimension and format checking
- **Metadata Management**: Filename, timestamp, and hash tracking
- **URL Generation**: Direct image URLs for dashboard use
- **Picture-Element Ready**: Perfect for interactive floor plans
- **Automation Support**: Full integration with Home Assistant automations

## 📋 Requirements

- **Home Assistant**: 2023.1 or later
- **Python Dependencies**: Pillow >= 8.0.0 (automatically installed)
- **Browser Support**: Modern browsers with ES6+ support
- **Storage**: Sufficient disk space for image storage

## 🚀 Quick Start

### Installation
1. Copy the `image_manager` folder to your `custom_components` directory
2. Restart Home Assistant
3. **Add the Lovelace resource** manually:
   - Go to **Settings** → **Dashboards** → **Resources**
   - Click "**Add Resource**" and add the following:
     - URL: `/hacsfiles/image_manager/image-manager.js` (Resource type: **JavaScript Module**)
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "Image Manager" and follow the setup wizard

### Basic Usage
1. Add the Image Manager card to your dashboard
2. Drag and drop 4K images onto the upload area
3. Use the generated entity IDs in your automations and cards

```yaml
# Example Lovelace card configuration
type: custom:image-manager-card
title: "My Images"
show_upload: true
show_gallery: true
columns: 3
```

## 📖 Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed installation instructions
- **[Usage Guide](USAGE.md)** - Comprehensive usage examples and best practices
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎨 Lovelace Card Configuration

The Image Manager card supports extensive customization:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "Image Manager" | Card title |
| `show_upload` | boolean | true | Show upload interface |
| `show_gallery` | boolean | true | Show image thumbnails |
| `show_entities` | boolean | true | Show entity ID list |
| `columns` | number | 3 | Gallery columns (1-6) |
| `thumbnail_size` | number | 150 | Thumbnail height in pixels |
| `target_input_text` | string | null | Input_text entity ID to set selected image URL to (enables selection mode) |

## 🖼️ Image Selector Card

A lightweight, standalone card designed for selecting an image and updating an `input_text` entity without showing the full management UI. It's perfect for dashboards where you only need to pick an image.

| Option              | Type    | Default | Description                                             |
|---------------------|---------|---------|---------------------------------------------------------|
| `target_input_text` | string  | **REQUIRED** | The `input_text` entity to update with the selected image URL. |
| `title`             | string  | "Image Selector" | A title for the card.                                   |
| `show_preview`      | boolean | true    | Show a preview of the currently selected image.         |

### Example Configuration

```yaml
type: custom:image-manager-selector-card
title: "Choose a Background"
target_input_text: input_text.dashboard_background_url
show_preview: true
```

### Usage Instructions
1.  Add the `image-manager-selector-card` to your Lovelace dashboard.
2.  Configure the `target_input_text` option with the ID of an `input_text` helper entity.
3.  When you click the "Select Image" button, a dialog will appear showing all available images from the Image Manager.
4.  Selecting an image will update the state of the `input_text` entity to that image's URL.

### Example Configuration

```yaml
type: custom:image-manager-card
title: "4K Image Gallery"
show_upload: true
show_gallery: true
show_entities: true
columns: 4
thumbnail_size: 200
```

### Example with Selection Mode

```yaml
type: custom:image-manager-card
title: "Select a Background"
show_upload: false
show_gallery: true
columns: 5
target_input_text: input_text.selected_image_url
```

## 🔌 Services

### `image_manager.upload_image`
Upload an image via service call:

```yaml
service: image_manager.upload_image
data:
  image_data: "base64_encoded_image_data"
  filename: "my_image.jpg"  # optional
```

### `image_manager.delete_image`
Delete a specific image:

```yaml
service: image_manager.delete_image
data:
  sequence: 1
```

### `image_manager.delete_all_images`
Clear all stored images:

```yaml
service: image_manager.delete_all_images
```

## 🌐 API Endpoints

The integration provides RESTful API endpoints:

- `GET /api/image_manager/status` - Get status and image list
- `POST /api/image_manager/upload` - Upload new images
- `POST /api/image_manager/delete` - Delete specific images
- `POST /api/image_manager/clear_all` - Delete all images
- `GET /api/image_manager/images/{sequence}` - Serve image files

## 🎯 Use Cases

### Dashboard Backgrounds
```yaml
# Use in picture-element cards
type: picture-elements
image: /api/image_manager/images/1
elements:
  - type: state-label
    entity: sensor.temperature
    style:
      top: 20%
      left: 50%
```

### Automation Triggers
```yaml
# Use image entities in automations
automation:
  - alias: "Update Dashboard Image"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: image_manager.upload_image
        data:
          image_data: "{{ states('sensor.weather_image_b64') }}"
```

### Template Usage
```yaml
# Reference images in templates
sensor:
  - platform: template
    sensors:
      current_image_url:
        value_template: "/api/image_manager/images/{{ states('input_number.current_image') | int }}"
```

## 📏 Image Specifications

- **Resolution**: Exactly 3840×2160 pixels (4K)
- **Formats**: JPEG, PNG input → JPEG output
- **Quality**: 95% JPEG compression
- **File Size**: Maximum 50MB per image
- **Storage**: Maximum 25 images total
- **Naming**: Automatic with sequence, timestamp, and hash

## 🔒 Security Considerations

- Images are stored locally on your Home Assistant server
- API endpoints require Home Assistant authentication
- No external services or cloud storage used
- File validation prevents malicious uploads
- Configurable storage limits prevent disk exhaustion

## 🛠️ Development

### File Structure
```
custom_components/image_manager/
├── __init__.py              # Main integration setup
├── config_flow.py           # Configuration flow
├── const.py                 # Constants and configuration
├── coordinator.py           # Data coordinator
├── image.py                 # Image entity implementation
├── image_storage.py         # Storage management
├── views.py                 # API endpoints
├── services.yaml            # Service definitions
├── manifest.json            # Integration manifest
├── translations/
│   └── en.json             # English translations
└── www/
    └── image-manager.js                # Consolidated frontend resources
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Check the detailed guides in the docs folder
- **Community**: Join the Home Assistant community forums

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - 4K image management
  - Lovelace card interface
  - Service integration
  - API endpoints

---

**Made with ❤️ for the Home Assistant community**