# Troubleshooting Guide - Image Manager Integration

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the Image Manager integration.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [Upload Failures](#upload-failures)
- [Card Display Issues](#card-display-issues)
- [Entity Problems](#entity-problems)
- [Service Call Errors](#service-call-errors)
- [Performance Issues](#performance-issues)
- [API Endpoint Problems](#api-endpoint-problems)
- [Log Analysis](#log-analysis)
- [Advanced Debugging](#advanced-debugging)
- [FAQ](#faq)

## Quick Diagnostics

### Health Check Checklist

Run through this checklist to quickly identify issues:

- [ ] Integration appears in **Settings** → **Devices & Services**
- [ ] Integration status shows "Configured" (not "Failed")
- [ ] Storage directory exists: `custom_components/image_manager/images/`
- [ ] Lovelace resources are loaded
- [ ] API endpoint responds: `/api/image_manager/status`
- [ ] No errors in Home Assistant logs

### System Status Commands

Check system status with these commands:

```bash
# Check integration files
ls -la config/custom_components/image_manager/

# Check storage directory
ls -la config/custom_components/image_manager/images/

# Check permissions
stat config/custom_components/image_manager/

# Check disk space
df -h config/
```

### Quick Fixes

Try these common solutions first:

1. **Restart Home Assistant** completely
2. **Clear browser cache** (Ctrl+F5)
3. **Check file permissions** on integration directory
4. **Verify 4K image dimensions** (3840×2160)
5. **Check available disk space**

## Installation Issues

### Integration Not Found

**Problem**: "Image Manager" doesn't appear in the integration list

**Symptoms**:
- Integration missing from **Add Integration** dialog
- No image_manager entries in logs
- Files appear to be in correct location

**Solutions**:

1. **Verify File Structure**:
   ```bash
   find config/custom_components/image_manager -name "*.py" | sort
   ```
   Should show 7 Python files.

2. **Check File Permissions**:
   ```bash
   chown -R homeassistant:homeassistant config/custom_components/image_manager
   chmod -R 755 config/custom_components/image_manager
   ```

3. **Validate manifest.json**:
   ```bash
   python3 -m json.tool config/custom_components/image_manager/manifest.json
   ```

4. **Complete Restart**:
   - Stop Home Assistant
   - Wait 30 seconds
   - Start Home Assistant
   - Check logs during startup

### Setup Failed Error

**Problem**: Integration setup fails during configuration

**Symptoms**:
- "Setup failed for image_manager" in logs
- Integration shows "Failed" status
- Configuration wizard doesn't complete

**Solutions**:

1. **Check Dependencies**:
   ```bash
   pip list | grep -i pillow
   ```
   Should show Pillow >= 8.0.0

2. **Manual Dependency Installation**:
   ```bash
   pip install Pillow>=8.0.0
   ```

3. **Storage Directory Creation**:
   ```bash
   mkdir -p config/custom_components/image_manager/images
   chown homeassistant:homeassistant config/custom_components/image_manager/images
   ```

4. **Check Available Memory**:
   ```bash
   free -h
   ```
   Ensure at least 512MB available RAM.

### Permission Denied Errors

**Problem**: Permission errors during setup or operation

**Symptoms**:
- "Permission denied" in logs
- Cannot create storage directory
- Cannot write image files

**Solutions**:

1. **Fix Ownership**:
   ```bash
   chown -R homeassistant:homeassistant config/custom_components/image_manager
   ```

2. **Fix Permissions**:
   ```bash
   chmod -R 755 config/custom_components/image_manager
   chmod -R 755 config/custom_components/image_manager/images
   ```

3. **SELinux Issues** (if applicable):
   ```bash
   setsebool -P httpd_can_network_connect 1
   restorecon -R config/custom_components/image_manager
   ```

## Configuration Problems

### Integration Won't Configure

**Problem**: Configuration wizard fails or doesn't save settings

**Symptoms**:
- Configuration dialog closes without saving
- Settings revert to defaults
- "Configuration invalid" errors

**Solutions**:

1. **Check Configuration Schema**:
   ```yaml
   # Valid configuration
   image_manager:
     name: "Image Manager"
     max_images: 25
   ```

2. **Reset Configuration**:
   - Remove integration from **Devices & Services**
   - Restart Home Assistant
   - Re-add integration

3. **Manual Configuration** (if needed):
   ```yaml
   # configuration.yaml
   image_manager:
     name: "My Images"
     max_images: 50
     storage_path: "/config/custom_images"
   ```

### Storage Path Issues

**Problem**: Custom storage path not working

**Symptoms**:
- Images not saving to custom location
- "Storage path not found" errors
- Permission denied on custom path

**Solutions**:

1. **Create Directory**:
   ```bash
   mkdir -p /path/to/custom/storage
   chown homeassistant:homeassistant /path/to/custom/storage
   chmod 755 /path/to/custom/storage
   ```

2. **Verify Path in Configuration**:
   ```yaml
   image_manager:
     storage_path: "/config/custom_images"  # Use absolute path
   ```

3. **Test Write Access**:
   ```bash
   sudo -u homeassistant touch /path/to/custom/storage/test.txt
   sudo -u homeassistant rm /path/to/custom/storage/test.txt
   ```

## Upload Failures

### Invalid Dimensions Error

**Problem**: "Invalid dimensions" error when uploading images

**Symptoms**:
- Upload fails with dimension error
- Images appear to be 4K but still rejected
- Inconsistent upload behavior

**Solutions**:

1. **Verify Exact Dimensions**:
   ```bash
   identify image.jpg  # Should show 3840x2160
   ```

2. **Resize Images**:
   ```bash
   # Using ImageMagick
   convert input.jpg -resize 3840x2160! output.jpg
   
   # Using FFmpeg
   ffmpeg -i input.jpg -vf scale=3840:2160 output.jpg
   ```

3. **Check Image Metadata**:
   ```bash
   exiftool image.jpg | grep -i dimension
   ```

4. **Batch Resize Script**:
   ```bash
   #!/bin/bash
   for img in *.jpg; do
     convert "$img" -resize 3840x2160! "resized_$img"
   done
   ```

### File Format Issues

**Problem**: "Unsupported format" error

**Symptoms**:
- JPEG/PNG files rejected
- Format appears correct but upload fails
- Inconsistent format detection

**Solutions**:

1. **Check Actual Format**:
   ```bash
   file image.jpg  # Should show JPEG or PNG
   ```

2. **Convert Format**:
   ```bash
   # Convert to JPEG
   convert input.png -quality 90 output.jpg
   
   # Convert to PNG
   convert input.jpg output.png
   ```

3. **Remove Metadata**:
   ```bash
   # Strip all metadata
   exiftool -all= image.jpg
   ```

### File Size Limitations

**Problem**: "File too large" error

**Symptoms**:
- Large files rejected
- Upload stops at certain file sizes
- Memory errors during upload

**Solutions**:

1. **Check File Size**:
   ```bash
   ls -lh image.jpg  # Should be under 50MB
   ```

2. **Compress Images**:
   ```bash
   # Reduce JPEG quality
   convert input.jpg -quality 75 output.jpg
   
   # Optimize PNG
   optipng -o7 image.png
   ```

3. **Batch Compression**:
   ```bash
   #!/bin/bash
   for img in *.jpg; do
     convert "$img" -quality 80 -resize 3840x2160! "compressed_$img"
   done
   ```

### Storage Full Error

**Problem**: "Storage full" error when uploading

**Symptoms**:
- Upload rejected due to storage limit
- Counter shows maximum images reached
- Cannot upload despite having disk space

**Solutions**:

1. **Check Current Usage**:
   ```bash
   ls -la config/custom_components/image_manager/images/ | wc -l
   ```

2. **Delete Old Images**:
   ```yaml
   # Via service call
   service: image_manager.delete_image
   data:
     sequence: 1
   ```

3. **Clear All Images**:
   ```yaml
   service: image_manager.delete_all_images
   ```

4. **Increase Storage Limit**:
   - Go to **Settings** → **Devices & Services**
   - Configure Image Manager
   - Increase max_images value

## Card Display Issues

### Card Not Appearing

**Problem**: Image Manager card doesn't show in dashboard

**Symptoms**:
- Card type not found in editor
- Blank space where card should be
- "Custom element doesn't exist" error

**Solutions**:

1. **Check Lovelace Resources**:
   - Go to **Settings** → **Dashboards** → **Resources**
   - Verify these entries exist:
     ```
     /hacsfiles/image_manager/image-manager-card.js (module)
     /hacsfiles/image_manager/image-manager-editor.js (module)
     ```

2. **Manual Resource Addition**:
   ```yaml
   # In Lovelace resources
   - url: /hacsfiles/image_manager/image-manager-card.js
     type: module
   - url: /hacsfiles/image_manager/image-manager-editor.js
     type: module
   ```

3. **Clear Browser Cache**:
   - Press Ctrl+F5 (or Cmd+Shift+R on Mac)
   - Or use browser developer tools to disable cache

4. **Check File Accessibility**:
   ```bash
   curl -I http://your-ha-url:8123/hacsfiles/image_manager/image-manager-card.js
   ```

### JavaScript Errors

**Problem**: Browser console shows JavaScript errors

**Symptoms**:
- Card loads but doesn't function
- Upload/delete buttons don't work
- Console shows script errors

**Solutions**:

1. **Check Browser Console**:
   - Press F12 to open developer tools
   - Look for errors in Console tab
   - Note specific error messages

2. **Update Browser**:
   - Ensure browser supports ES6+ features
   - Chrome 60+, Firefox 63+, Safari 12+, Edge 79+

3. **Disable Browser Extensions**:
   - Try in incognito/private mode
   - Disable ad blockers temporarily

4. **Check Network Tab**:
   - Verify all resources load successfully
   - Look for 404 or 500 errors

### Card Configuration Errors

**Problem**: Card configuration doesn't save or apply

**Symptoms**:
- Configuration reverts to defaults
- Options don't take effect
- Editor shows validation errors

**Solutions**:

1. **Validate YAML Syntax**:
   ```yaml
   # Correct format
   type: custom:image-manager-card
   title: "My Images"
   columns: 3
   thumbnail_size: 150
   ```

2. **Check Option Values**:
   - `columns`: 1-6
   - `thumbnail_size`: 100, 150, 200, 250
   - `show_*`: true/false

3. **Reset Card Configuration**:
   - Delete card from dashboard
   - Add new card with default settings
   - Gradually add custom options

## Entity Problems

### Entities Not Created

**Problem**: Image entities don't appear after upload

**Symptoms**:
- Upload succeeds but no entities created
- Entity registry doesn't show image entities
- Cannot reference entities in automations

**Solutions**:

1. **Check Entity Registry**:
   - Go to **Settings** → **Devices & Services** → **Entities**
   - Search for "image_manager"

2. **Force Entity Refresh**:
   ```yaml
   service: homeassistant.reload_config_entry
   target:
     entity_id: image_manager
   ```

3. **Manual Entity Creation**:
   ```yaml
   # configuration.yaml
   image:
     - platform: local_file
       file_path: /config/custom_components/image_manager/images/img_001_*.jpg
       name: "Image Manager 1"
   ```

### Entity States Incorrect

**Problem**: Entity states show wrong values or "unavailable"

**Symptoms**:
- Entities show "unavailable" state
- Image URLs are incorrect
- Entity attributes missing

**Solutions**:

1. **Check File Existence**:
   ```bash
   ls -la config/custom_components/image_manager/images/
   ```

2. **Verify File Permissions**:
   ```bash
   chmod 644 config/custom_components/image_manager/images/*.jpg
   ```

3. **Restart Integration**:
   - Go to **Settings** → **Devices & Services**
   - Find Image Manager integration
   - Click **Reload**

### Entity Naming Issues

**Problem**: Entity names or IDs are incorrect

**Symptoms**:
- Unexpected entity naming patterns
- Duplicate entity IDs
- Entity names don't match configuration

**Solutions**:

1. **Check Entity ID Pattern**:
   - Should be: `image.image_manager_1`, `image.image_manager_2`, etc.

2. **Rename Entities**:
   - Go to **Settings** → **Devices & Services** → **Entities**
   - Find image_manager entities
   - Click entity to rename

3. **Reset Entity Registry**:
   ```bash
   # Stop Home Assistant
   rm config/.storage/core.entity_registry
   # Start Home Assistant (entities will be recreated)
   ```

## Service Call Errors

### Service Not Found

**Problem**: "Service image_manager.* not found" errors

**Symptoms**:
- Service calls fail with "not found" error
- Services don't appear in developer tools
- Automation service calls fail

**Solutions**:

1. **Check Service Registration**:
   - Go to **Developer Tools** → **Services**
   - Search for "image_manager"

2. **Reload Integration**:
   ```yaml
   service: homeassistant.reload_config_entry
   target:
     entity_id: image_manager
   ```

3. **Restart Home Assistant**:
   - Complete restart may be needed for service registration

### Invalid Service Data

**Problem**: Service calls fail with data validation errors

**Symptoms**:
- "Invalid service data" errors
- Required parameters missing
- Data format errors

**Solutions**:

1. **Check Service Schema**:
   ```yaml
   # Correct upload service call
   service: image_manager.upload_image
   data:
     image_data: "base64_encoded_data_here"
     filename: "optional_filename.jpg"
   ```

2. **Validate Base64 Data**:
   ```bash
   # Test base64 data
   echo "your_base64_data" | base64 -d > test_image.jpg
   file test_image.jpg  # Should show image format
   ```

3. **Use Service Developer Tools**:
   - Go to **Developer Tools** → **Services**
   - Select service and fill in data
   - Test before using in automations

### Base64 Encoding Issues

**Problem**: Base64 image data is invalid or corrupted

**Symptoms**:
- "Invalid image data" errors
- Upload fails with encoding errors
- Corrupted images after upload

**Solutions**:

1. **Validate Base64 Format**:
   ```python
   import base64
   try:
       decoded = base64.b64decode(your_base64_data)
       print("Valid base64")
   except:
       print("Invalid base64")
   ```

2. **Proper Base64 Encoding**:
   ```bash
   # Encode image file
   base64 -w 0 image.jpg > image_b64.txt
   ```

3. **Remove Data URL Prefix**:
   ```python
   # Remove "data:image/jpeg;base64," prefix if present
   if base64_data.startswith('data:'):
       base64_data = base64_data.split(',')[1]
   ```

## Performance Issues

### Slow Upload Performance

**Problem**: Image uploads are very slow

**Symptoms**:
- Uploads take several minutes
- Browser becomes unresponsive
- Timeout errors during upload

**Solutions**:

1. **Optimize Image Size**:
   ```bash
   # Compress before upload
   convert input.jpg -quality 80 -resize 3840x2160! output.jpg
   ```

2. **Check Network Speed**:
   ```bash
   # Test upload speed to Home Assistant
   curl -X POST -F "file=@test.jpg" http://your-ha-url:8123/test
   ```

3. **Increase Timeout Settings**:
   ```yaml
   # configuration.yaml
   http:
     server_timeout: 300
   ```

4. **Monitor System Resources**:
   ```bash
   # Check CPU and memory usage during upload
   top -p $(pgrep -f "home-assistant")
   ```

### High Memory Usage

**Problem**: Home Assistant uses excessive memory during image processing

**Symptoms**:
- Memory usage spikes during uploads
- System becomes slow or unresponsive
- Out of memory errors

**Solutions**:

1. **Monitor Memory Usage**:
   ```bash
   # Check memory usage
   free -h
   ps aux | grep home-assistant
   ```

2. **Reduce Image Quality**:
   ```bash
   # Lower quality to reduce memory usage
   convert input.jpg -quality 70 -resize 3840x2160! output.jpg
   ```

3. **Limit Concurrent Uploads**:
   - Upload one image at a time
   - Wait for completion before next upload

4. **Increase System Memory**:
   - Add more RAM if possible
   - Use swap file as temporary solution

### Slow Card Loading

**Problem**: Lovelace card loads slowly or times out

**Symptoms**:
- Card takes long time to appear
- Thumbnails load slowly
- Browser becomes unresponsive

**Solutions**:

1. **Reduce Thumbnail Size**:
   ```yaml
   type: custom:image-manager-card
   thumbnail_size: 100  # Smaller thumbnails
   columns: 6
   ```

2. **Limit Displayed Images**:
   ```yaml
   type: custom:image-manager-card
   show_gallery: false  # Hide gallery if not needed
   show_entities: true
   ```

3. **Use Conditional Cards**:
   ```yaml
   type: conditional
   conditions:
     - entity: input_boolean.show_images
       state: "on"
   card:
     type: custom:image-manager-card
   ```

## API Endpoint Problems

### API Not Responding

**Problem**: API endpoints return errors or don't respond

**Symptoms**:
- 404 errors on API calls
- Timeout errors
- "Service unavailable" responses

**Solutions**:

1. **Check API Endpoint Registration**:
   ```bash
   # Test status endpoint
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://your-ha-url:8123/api/image_manager/status
   ```

2. **Verify Integration Status**:
   - Ensure integration is "Configured" not "Failed"
   - Check for setup errors in logs

3. **Test Authentication**:
   ```bash
   # Get long-lived access token
   curl -X POST -H "Content-Type: application/json" \
        -d '{"username":"your_user","password":"your_pass"}' \
        http://your-ha-url:8123/auth/token
   ```

### CORS Issues

**Problem**: Cross-origin request errors when accessing API

**Symptoms**:
- CORS errors in browser console
- API calls fail from external applications
- "Access-Control-Allow-Origin" errors

**Solutions**:

1. **Configure CORS**:
   ```yaml
   # configuration.yaml
   http:
     cors_allowed_origins:
       - "http://localhost:3000"
       - "https://your-external-app.com"
   ```

2. **Use Proper Headers**:
   ```javascript
   // JavaScript API call
   fetch('/api/image_manager/status', {
     headers: {
       'Authorization': 'Bearer ' + token,
       'Content-Type': 'application/json'
     }
   })
   ```

### Authentication Failures

**Problem**: API calls fail with authentication errors

**Symptoms**:
- 401 Unauthorized errors
- "Invalid token" messages
- Authentication required errors

**Solutions**:

1. **Generate Long-Lived Token**:
   - Go to **Profile** → **Long-Lived Access Tokens**
   - Create new token for API access

2. **Use Correct Header Format**:
   ```bash
   curl -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" \
        http://your-ha-url:8123/api/image_manager/status
   ```

3. **Check Token Validity**:
   ```bash
   # Test token with simple API call
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://your-ha-url:8123/api/states
   ```

## Log Analysis

### Finding Relevant Logs

**Location**: **Settings** → **System** → **Logs**

**Search Terms**:
- `image_manager`
- `custom_components.image_manager`
- `Pillow`
- `upload`
- `delete`

### Common Log Messages

#### Successful Operations
```
[custom_components.image_manager] Image uploaded successfully: sequence 1
[custom_components.image_manager] Image deleted successfully: sequence 1
[custom_components.image_manager] Integration setup completed
```

#### Error Messages
```
[custom_components.image_manager] Setup failed: Permission denied
[custom_components.image_manager] Invalid image dimensions: 1920x1080
[custom_components.image_manager] Storage full: 25/25 images
[custom_components.image_manager] Unsupported format: GIF
```

### Log Level Configuration

Increase logging detail for troubleshooting:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.image_manager: debug
    PIL: debug
```

### Log File Analysis

For detailed analysis, check log files directly:

```bash
# View recent logs
tail -f config/home-assistant.log | grep image_manager

# Search for specific errors
grep -i "error" config/home-assistant.log | grep image_manager

# Check startup logs
grep -A 10 -B 10 "image_manager" config/home-assistant.log
```

## Advanced Debugging

### Python Debug Mode

Enable debug mode for detailed troubleshooting:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.image_manager: debug
    homeassistant.components.image: debug
    PIL.Image: debug
```

### Integration State Inspection

Check integration state in developer tools:

```python
# Developer Tools > Templates
{{ states.image | selectattr('entity_id', 'match', 'image.image_manager_.*') | list }}
{{ integration_entities('image_manager') }}
```

### File System Debugging

Check file system state:

```bash
# Check storage directory
find config/custom_components/image_manager/images -type f -name "*.jpg" -exec ls -la {} \;

# Check metadata file
cat config/custom_components/image_manager/images/metadata.json

# Check disk usage
du -sh config/custom_components/image_manager/images/
```

### Network Debugging

Debug network issues:

```bash
# Check port accessibility
netstat -tlnp | grep :8123

# Test local connectivity
curl -I http://localhost:8123/api/image_manager/status

# Check firewall rules
iptables -L | grep 8123
```

### Memory and Performance Profiling

Monitor resource usage:

```bash
# Monitor Home Assistant process
top -p $(pgrep -f home-assistant)

# Check memory usage over time
while true; do
  ps aux | grep home-assistant | grep -v grep
  sleep 5
done

# Monitor disk I/O
iotop -p $(pgrep -f home-assistant)
```

## FAQ

### General Questions

**Q: Can I use images other than 4K resolution?**
A: No, the integration is specifically designed for 3840×2160 (4K) images only. This ensures consistency and optimal performance.

**Q: Why is there a 25 image limit?**
A: The default limit prevents excessive disk usage. You can increase this limit in the integration configuration up to 100 images.

**Q: Can I store images outside the integration directory?**
A: Yes, you can configure a custom storage path in the integration settings.

### Technical Questions

**Q: What happens to images when I uninstall the integration?**
A: Images remain in the storage directory but entities are removed. You should manually delete the images directory if desired.

**Q: Can I access images from outside Home Assistant?**
A: Images are served through Home Assistant's authentication system. External access requires proper authentication tokens.

**Q: Why do uploads sometimes fail silently?**
A: Check the browser console for JavaScript errors and Home Assistant logs for backend errors. Common causes are dimension validation failures or storage limits.

### Performance Questions

**Q: Why is image processing slow?**
A: Image processing requires significant CPU and memory. Consider reducing image quality or upgrading hardware for better performance.

**Q: Can I upload multiple images simultaneously?**
A: While possible, it's recommended to upload one image at a time to avoid memory issues and ensure reliable processing.

**Q: How can I optimize storage usage?**
A: Use JPEG format with 80-90% quality, implement regular cleanup routines, and monitor storage usage with automations.

### Integration Questions

**Q: Can I use Image Manager with other integrations?**
A: Yes, images can be used in any Home Assistant component that accepts image URLs, including picture-element cards, notifications, and automations.

**Q: How do I backup my images?**
A: Include the `custom_components/image_manager/images/` directory in your Home Assistant backup routine.

**Q: Can I migrate images between Home Assistant instances?**
A: Yes, copy the entire `images` directory and `metadata.json` file to the new instance after installing the integration.

## Getting Help

If this troubleshooting guide doesn't resolve your issue:

1. **Check the [Installation Guide](INSTALLATION.md)** for setup issues
2. **Review the [Usage Guide](USAGE.md)** for configuration help
3. **Search existing issues** on the GitHub repository
4. **Create a detailed issue report** with:
   - Home Assistant version
   - Integration version
   - Complete error logs
   - Steps to reproduce
   - System information

### Issue Report Template

```
**Home Assistant Version**: 2023.x.x
**Integration Version**: 1.0.0
**Browser**: Chrome/Firefox/Safari version
**Operating System**: Linux/Windows/macOS

**Problem Description**:
[Describe the issue clearly]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [Third step]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Logs**:
```
[Paste relevant log entries here]
```

**Additional Context**:
[Any other relevant information]
```

---

**Remember**: Most issues can be resolved by checking file permissions, verifying image dimensions, and ensuring proper installation. When in doubt, restart Home Assistant and clear your browser cache!