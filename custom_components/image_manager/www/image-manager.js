/* Image Manager Card */
class ImageManagerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._images = [];
    this._uploading = false;
    this._dragCounter = 0;
    this._initialized = false;
    this._loadingPromise = null;
    this._lastLoadTime = 0;
  }

  static getConfigElement() {
    return document.createElement('image-manager-card-editor');
  }

  static getStubConfig() {
    return {
      type: 'custom:image-manager-card',
      title: 'Image Manager',
      show_upload: true,
      show_gallery: true,
      show_entities: true,
      columns: 3,
      thumbnail_size: 150,
      target_input_text: null
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this._config = {
      title: 'Image Manager',
      show_upload: true,
      show_gallery: true,
      show_entities: true,
      columns: 3,
      thumbnail_size: 150,
      target_input_text: null,
      ...config
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Only load images if this is the first time hass is set or if explicitly needed
    if (!this._initialized) {
      this._initialized = true;
      this._loadImages();
    }
  }

  async _loadImages() {
    if (!this._hass) return;

    const now = Date.now();
    // Prevent loading more than once every 5 seconds
    if (now - this._lastLoadTime < 5000) {
      return;
    }

    // If already loading, wait for the existing request
    if (this._loadingPromise) {
      return this._loadingPromise;
    }

    this._lastLoadTime = now;
    this._loadingPromise = (async () => {
      try {
        const response = await this._hass.callApi('GET', 'image_manager/status');
        const newImages = response.images || [];
        this._maxImages = response.max_images || 25;
        this._storageFull = response.storage_full || false;

        // Smart loading: only update if there are actual changes
        const currentSequences = new Set(this._images.map(img => img.sequence));
        const newSequences = new Set(newImages.map(img => img.sequence));

        const hasNewImages = newImages.some(img => !currentSequences.has(img.sequence));
        const hasRemovedImages = this._images.some(img => !newSequences.has(img.sequence));

        if (hasNewImages || hasRemovedImages) {
          this._images = newImages;
          this._render();
        }
      } catch (error) {
        console.error('Failed to load images:', error);
        this._showError('Failed to load images');
      } finally {
        this._loadingPromise = null;
      }
    })();

    return this._loadingPromise;
  }

  _render() {
    if (!this.shadowRoot) return;

    const style = `
      <style>
        :host {
          display: block;
          background: var(--card-background-color);
          border-radius: var(--ha-card-border-radius);
          box-shadow: var(--ha-card-box-shadow);
          padding: 16px;
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          font-size: 1.2em;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .storage-info {
          font-size: 0.9em;
          color: var(--secondary-text-color);
        }
        
        .upload-area {
          border: 2px dashed var(--divider-color);
          border-radius: 8px;
          padding: 32px;
          text-align: center;
          margin-bottom: 16px;
          transition: all 0.3s ease;
          cursor: pointer;
          position: relative;
        }
        
        .upload-area:hover,
        .upload-area.drag-over {
          border-color: var(--primary-color);
          background-color: var(--primary-color-alpha-10);
        }
        
        .upload-area.uploading {
          pointer-events: none;
          opacity: 0.6;
        }
        
        .upload-icon {
          font-size: 48px;
          color: var(--secondary-text-color);
          margin-bottom: 16px;
        }
        
        .upload-text {
          color: var(--primary-text-color);
          margin-bottom: 8px;
        }
        
        .upload-subtext {
          color: var(--secondary-text-color);
          font-size: 0.9em;
        }
        
        .file-input {
          display: none;
        }
        
        .progress-bar {
          width: 100%;
          height: 4px;
          background-color: var(--divider-color);
          border-radius: 2px;
          overflow: hidden;
          margin-top: 16px;
        }
        
        .progress-fill {
          height: 100%;
          background-color: var(--primary-color);
          transition: width 0.3s ease;
        }
        
        .gallery {
          display: grid;
          grid-template-columns: repeat(var(--columns), 1fr);
          gap: 16px;
          margin-bottom: 16px;
        }
        
        .image-item {
          position: relative;
          border-radius: 8px;
          overflow: hidden;
          background: var(--card-background-color);
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          transition: transform 0.2s ease;
        }
        
        .image-item:hover {
          transform: translateY(-2px);
        }
        
        .image-thumbnail {
          width: 100%;
          height: var(--thumbnail-size);
          object-fit: cover;
          display: block;
        }
        
        .image-info {
          padding: 8px;
          font-size: 0.8em;
          color: var(--secondary-text-color);
        }
        
        .image-actions {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          gap: 4px;
          opacity: 0;
          transition: opacity 0.2s ease;
        }
        
        .image-item:hover .image-actions {
          opacity: 1;
        }
        
        .action-button {
          background: rgba(0,0,0,0.7);
          border: none;
          border-radius: 4px;
          color: white;
          padding: 4px 8px;
          cursor: pointer;
          font-size: 12px;
          transition: background-color 0.2s ease;
        }
        
        .action-button:hover {
          background: rgba(0,0,0,0.9);
        }
        
        .action-button.delete {
          background: rgba(244, 67, 54, 0.8);
        }
        
        .action-button.delete:hover {
          background: rgba(244, 67, 54, 1);
        }
        
        .action-button.select {
          background: var(--primary-color);
        }
        
        .action-button.select:hover {
          background: var(--primary-color-dark);
        }
        
        .entities-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color);
        }
        
        .entities-title {
          font-weight: 500;
          margin-bottom: 8px;
          color: var(--primary-text-color);
        }
        
        .entity-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background: var(--secondary-background-color);
          border-radius: 4px;
          margin-bottom: 4px;
        }
        
        .entity-id {
          font-family: monospace;
          font-size: 0.9em;
          color: var(--primary-text-color);
        }
        
        .copy-button {
          background: var(--primary-color);
          border: none;
          border-radius: 4px;
          color: white;
          padding: 4px 8px;
          cursor: pointer;
          font-size: 12px;
        }
        
        .management-actions {
          display: flex;
          gap: 8px;
          margin-top: 16px;
        }
        
        .management-button {
          background: var(--primary-color);
          border: none;
          border-radius: 4px;
          color: white;
          padding: 8px 16px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.2s ease;
        }
        
        .management-button:hover {
          background: var(--primary-color-dark);
        }
        
        .management-button.danger {
          background: var(--error-color);
        }
        
        .management-button.danger:hover {
          background: var(--error-color-dark);
        }
        
        .error-message {
          background: var(--error-color);
          color: white;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 16px;
        }
        
        .success-message {
          background: var(--success-color);
          color: white;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 16px;
        }
        
        .empty-state {
          text-align: center;
          padding: 32px;
          color: var(--secondary-text-color);
        }
        
        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }
      </style>
    `;

    const content = `
      ${this._config.title ? `<div class="card-header">
        <span>${this._config.title}</span>
        <span class="storage-info">${this._images.length}/${this._maxImages} images</span>
      </div>` : ''}
      
      ${this._renderMessages()}
      
      ${this._config.show_upload ? this._renderUploadArea() : ''}
      
      ${this._config.show_gallery ? this._renderGallery() : ''}
      
      ${this._config.show_entities ? this._renderEntities() : ''}
      
      ${this._renderManagementActions()}
    `;

    this.shadowRoot.innerHTML = style + content;
    this._attachEventListeners();
  }

  _renderMessages() {
    if (this._errorMessage) {
      return `<div class="error-message">${this._errorMessage}</div>`;
    }
    if (this._successMessage) {
      return `<div class="success-message">${this._successMessage}</div>`;
    }
    return '';
  }

  _renderUploadArea() {
    if (this._storageFull) {
      return `
        <div class="upload-area" style="border-color: var(--error-color); background-color: var(--error-color-alpha-10);">
          <div class="upload-icon">⚠️</div>
          <div class="upload-text">Storage Full</div>
          <div class="upload-subtext">Delete some images to upload new ones</div>
        </div>
      `;
    }

    return `
      <div class="upload-area ${this._uploading ? 'uploading' : ''}" id="upload-area">
        <div class="upload-icon">${this._uploading ? '⏳' : '📁'}</div>
        <div class="upload-text">
          ${this._uploading ? 'Uploading...' : 'Drop images or PDFs here or click to browse'}
        </div>
        <div class="upload-subtext">
          ${this._uploading ? 'Please wait...' : 'Supports 4K images (3840×2160) and PDF files'}
        </div>
        ${this._uploading ? '<div class="progress-bar"><div class="progress-fill" style="width: 50%"></div></div>' : ''}
        <input type="file" class="file-input" id="file-input" accept="image/*,application/pdf" multiple>
      </div>
    `;
  }

  _renderGallery() {
    if (this._images.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-icon">🖼️</div>
          <div>No images uploaded yet</div>
        </div>
      `;
    }

    const columns = this._config.columns || 3;
    const thumbnailSize = this._config.thumbnail_size || 150;

    return `
      <div class="gallery" style="--columns: ${columns}; --thumbnail-size: ${thumbnailSize}px;">
        ${this._images.map(image => {
          const actionButton = this._config.target_input_text
            ? `<button class="action-button select" data-action="select" data-url="${image.url}" data-sequence="${image.sequence}">Select</button>`
            : `<button class="action-button copy" data-action="copy-url" data-url="${image.url}">Copy URL</button>`;
          
          return `
            <div class="image-item">
              <img class="image-thumbnail" src="${image.url}" alt="${image.filename}" loading="lazy">
              <div class="image-actions">
                ${actionButton}
                <button class="action-button delete" data-action="delete" data-sequence="${image.sequence}">Delete</button>
              </div>
              <div class="image-info">
                <div>${image.filename}</div>
                <div>Sequence: ${image.sequence}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  _renderEntities() {
    if (this._images.length === 0) return '';

    return `
      <div class="entities-section">
        <div class="entities-title">Entity IDs</div>
        ${this._images.map(image => `
          <div class="entity-item">
            <span class="entity-id">${image.entity_id}</span>
            <button class="copy-button" data-action="copy-entity" data-entity="${image.entity_id}">Copy</button>
          </div>
        `).join('')}
      </div>
    `;
  }

  _renderManagementActions() {
    if (this._images.length === 0) return '';

    return `
      <div class="management-actions">
        <button class="management-button danger" data-action="clear-all">Clear All Images</button>
        <button class="management-button" data-action="refresh">Refresh</button>
      </div>
    `;
  }

  _attachEventListeners() {
    const uploadArea = this.shadowRoot.getElementById('upload-area');
    const fileInput = this.shadowRoot.getElementById('file-input');

    if (uploadArea && fileInput) {
      // Upload area click
      uploadArea.addEventListener('click', () => {
        if (!this._uploading && !this._storageFull) {
          fileInput.click();
        }
      });

      // File input change
      fileInput.addEventListener('change', (e) => {
        this._handleFiles(e.target.files);
      });

      // Drag and drop
      uploadArea.addEventListener('dragenter', this._handleDragEnter.bind(this));
      uploadArea.addEventListener('dragover', this._handleDragOver.bind(this));
      uploadArea.addEventListener('dragleave', this._handleDragLeave.bind(this));
      uploadArea.addEventListener('drop', this._handleDrop.bind(this));
    }

    // Action buttons
    this.shadowRoot.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      if (!action) return;

      switch (action) {
        case 'copy-url':
          this._copyToClipboard(e.target.dataset.url);
          break;
        case 'copy-entity':
          this._copyToClipboard(e.target.dataset.entity);
          break;
        case 'delete':
          this._deleteImage(parseInt(e.target.dataset.sequence));
          break;
        case 'select':
          this._selectImage(e.target.dataset.url);
          break;
        case 'clear-all':
         this._clearAllImages();
         break;
        case 'refresh':
          this._loadImages();
          break;
      }
    });
  }

  _handleDragEnter(e) {
    e.preventDefault();
    this._dragCounter++;
    e.currentTarget.classList.add('drag-over');
  }

  _handleDragOver(e) {
    e.preventDefault();
  }

  _handleDragLeave(e) {
    e.preventDefault();
    this._dragCounter--;
    if (this._dragCounter === 0) {
      e.currentTarget.classList.remove('drag-over');
    }
  }

  _handleDrop(e) {
    e.preventDefault();
    this._dragCounter = 0;
    e.currentTarget.classList.remove('drag-over');
    
    if (this._uploading || this._storageFull) return;
    
    const files = e.dataTransfer.files;
    this._handleFiles(files);
  }

  async _handleFiles(files) {
    if (!files || files.length === 0) return;

    for (const file of files) {
      await this._uploadFile(file);
    }
  }

  async _uploadFile(file) {
    if (this._uploading) return;

    // Validate file type - accept images and PDFs
    const isImage = file.type.startsWith('image/');
    const isPDF = file.type === 'application/pdf';
    
    if (!isImage && !isPDF) {
      this._showError('Please select an image file or PDF');
      return;
    }

    // Validate dimensions only for images (PDFs will be converted)
    if (isImage) {
      const dimensions = await this._getImageDimensions(file);
      if (dimensions.width !== 3840 || dimensions.height !== 2160) {
        this._showError(`Image must be exactly 3840×2160 pixels. Got ${dimensions.width}×${dimensions.height}`);
        return;
      }
    }

    this._uploading = true;
    this._clearMessages();
    this._render();

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('filename', file.name);

      // Use direct fetch instead of hass.callApi for multipart uploads
      const response = await fetch('/api/image_manager/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this._hass.auth.data.access_token}`,
        },
        body: formData
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        this._showSuccess('Image uploaded successfully');
        await this._loadImages();
      } else {
        this._showError(result.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      this._showError('Upload failed: ' + error.message);
    } finally {
      this._uploading = false;
      this._render();
    }
  }

  _getImageDimensions(file) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        resolve({ width: img.width, height: img.height });
      };
      img.src = URL.createObjectURL(file);
    });
  }

  async _deleteImage(sequence) {
    if (!confirm('Are you sure you want to delete this image?')) return;

    try {
      const response = await this._hass.callApi('POST', 'image_manager/delete', { sequence });
      
      if (response.success) {
        this._showSuccess('Image deleted successfully');
        await this._loadImages();
      } else {
        this._showError(response.error || 'Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      this._showError('Delete failed: ' + error.message);
    }
  }

  async _clearAllImages() {
    if (!confirm('Are you sure you want to delete ALL images? This cannot be undone.')) return;

    try {
      const response = await this._hass.callApi('POST', 'image_manager/clear_all');
      
      if (response.success) {
        this._showSuccess(`Deleted ${response.deleted_count} images`);
        await this._loadImages();
      } else {
        this._showError(response.error || 'Clear all failed');
      }
    } catch (error) {
      console.error('Clear all error:', error);
      this._showError('Clear all failed: ' + error.message);
    }
  }

  async _selectImage(url) {
    const entityId = this._config.target_input_text;
    if (!entityId) {
      this._showError('Target input_text entity not configured.');
      return;
    }

    if (!this._hass.states[entityId]) {
      this._showError(`Entity not found: ${entityId}`);
      return;
    }

    try {
      await this._hass.callService('input_text', 'set_value', {
        entity_id: entityId,
        value: url,
      });
      this._showSuccess(`Image URL set for ${entityId}`);
    } catch (error) {
      console.error('Failed to set input_text value:', error);
      this._showError('Failed to set image URL.');
    }
  }

  _copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      this._showSuccess('Copied to clipboard');
    }).catch(() => {
      this._showError('Failed to copy to clipboard');
    });
  }

  _showError(message) {
    this._errorMessage = message;
    this._successMessage = null;
    this._render();
    setTimeout(() => {
      this._clearMessages();
      this._render();
    }, 5000);
  }

  _showSuccess(message) {
    this._successMessage = message;
    this._errorMessage = null;
    this._render();
    setTimeout(() => {
      this._clearMessages();
      this._render();
    }, 3000);
  }

  _clearMessages() {
    this._errorMessage = null;
    this._successMessage = null;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('image-manager-card', ImageManagerCard);

// Register the card with the card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'image-manager-card',
  name: 'Image Manager Card',
  description: 'A card for managing 4K images with upload and gallery features',
  preview: true,
});

console.info(
  `%c  IMAGE-MANAGER-CARD  %c  Version 1.0.1  `,
  'color: orange; font-weight: bold; background: black',
  'color: white; font-weight: bold; background: dimgray',
);

/* Image Manager Card Editor */
class ImageManagerCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _render() {
    if (!this.shadowRoot) return;

    const style = `
      <style>
        :host {
          display: block;
        }
        
        .card-config {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .config-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          min-height: 40px;
        }
        
        .config-label {
          font-weight: 500;
          color: var(--primary-text-color);
          min-width: 120px;
        }
        
        .config-input {
          flex: 1;
          margin-left: 16px;
        }
        
        .config-input input,
        .config-input select {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font-size: 14px;
        }
        
        .config-input input:focus,
        .config-input select:focus {
          outline: none;
          border-color: var(--primary-color);
        }
        
        .config-input input[type="number"] {
          max-width: 100px;
        }
        
        .toggle-switch {
          position: relative;
          display: inline-block;
          width: 50px;
          height: 24px;
        }
        
        .toggle-switch input {
          opacity: 0;
          width: 0;
          height: 0;
        }
        
        .slider {
          position: absolute;
          cursor: pointer;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: var(--divider-color);
          transition: 0.3s;
          border-radius: 24px;
        }
        
        .slider:before {
          position: absolute;
          content: "";
          height: 18px;
          width: 18px;
          left: 3px;
          bottom: 3px;
          background-color: white;
          transition: 0.3s;
          border-radius: 50%;
        }
        
        input:checked + .slider {
          background-color: var(--primary-color);
        }
        
        input:checked + .slider:before {
          transform: translateX(26px);
        }
        
        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--primary-text-color);
          margin: 24px 0 12px 0;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--divider-color);
        }
        
        .section-title:first-child {
          margin-top: 0;
        }
        
        .help-text {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 4px;
          line-height: 1.4;
        }
        
        .preview-section {
          margin-top: 24px;
          padding: 16px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }
        
        .preview-title {
          font-weight: 500;
          margin-bottom: 12px;
          color: var(--primary-text-color);
        }
        
        .preview-config {
          font-family: monospace;
          font-size: 12px;
          background: var(--card-background-color);
          padding: 12px;
          border-radius: 4px;
          border: 1px solid var(--divider-color);
          white-space: pre-wrap;
          color: var(--primary-text-color);
          max-height: 200px;
          overflow-y: auto;
        }
      </style>
    `;

    const content = `
      <div class="card-config">
        <div class="section-title">Basic Settings</div>
        
        <div class="config-row">
          <label class="config-label">Title</label>
          <div class="config-input">
            <input 
              type="text" 
              id="title" 
              value="${this._config.title || 'Image Manager'}"
              placeholder="Image Manager"
            >
            <div class="help-text">The title displayed at the top of the card</div>
          </div>
        </div>

        <div class="section-title">Display Options</div>
        
        <div class="config-row">
          <label class="config-label">Show Upload Area</label>
          <div class="config-input">
            <label class="toggle-switch">
              <input type="checkbox" id="show_upload" ${this._config.show_upload !== false ? 'checked' : ''}>
              <span class="slider"></span>
            </label>
            <div class="help-text">Show the drag-and-drop upload area</div>
          </div>
        </div>
        
        <div class="config-row">
          <label class="config-label">Show Gallery</label>
          <div class="config-input">
            <label class="toggle-switch">
              <input type="checkbox" id="show_gallery" ${this._config.show_gallery !== false ? 'checked' : ''}>
              <span class="slider"></span>
            </label>
            <div class="help-text">Show the image gallery with thumbnails</div>
          </div>
        </div>
        
        <div class="config-row">
          <label class="config-label">Show Entity IDs</label>
          <div class="config-input">
            <label class="toggle-switch">
              <input type="checkbox" id="show_entities" ${this._config.show_entities !== false ? 'checked' : ''}>
              <span class="slider"></span>
            </label>
            <div class="help-text">Show the list of entity IDs for easy copying</div>
          </div>
        </div>

        <div class="section-title">Gallery Settings</div>
        
        <div class="config-row">
          <label class="config-label">Columns</label>
          <div class="config-input">
            <input 
              type="number" 
              id="columns" 
              value="${this._config.columns || 3}"
              min="1" 
              max="6"
            >
            <div class="help-text">Number of columns in the image gallery (1-6)</div>
          </div>
        </div>
        
        <div class="config-row">
          <label class="config-label">Thumbnail Size</label>
          <div class="config-input">
            <select id="thumbnail_size">
              <option value="100" ${this._config.thumbnail_size === 100 ? 'selected' : ''}>Small (100px)</option>
              <option value="150" ${(this._config.thumbnail_size || 150) === 150 ? 'selected' : ''}>Medium (150px)</option>
              <option value="200" ${this._config.thumbnail_size === 200 ? 'selected' : ''}>Large (200px)</option>
              <option value="250" ${this._config.thumbnail_size === 250 ? 'selected' : ''}>Extra Large (250px)</option>
            </select>
            <div class="help-text">Height of thumbnail images in the gallery</div>
          </div>
        </div>

        <div class="section-title">Selection Mode</div>

        <div class="config-row">
          <label class="config-label">Target Input Text</label>
          <div class="config-input">
            <input
              type="text"
              id="target_input_text"
              value="${this._config.target_input_text || ''}"
              placeholder="input_text.my_input"
            >
            <div class="help-text">Optional: Entity ID of input_text helper to set selected image URL to</div>
          </div>
        </div>

        <div class="preview-section">
          <div class="preview-title">Configuration Preview</div>
          <div class="preview-config" id="config-preview"></div>
        </div>
      </div>
    `;

    this.shadowRoot.innerHTML = style + content;
    this._attachEventListeners();
    this._updatePreview();
  }

  _attachEventListeners() {
    // Text inputs
    const textInputs = ['title', 'target_input_text'];
    textInputs.forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('input', (e) => {
          this._updateConfig(id, e.target.value);
        });
      }
    });

    // Number inputs
    const numberInputs = ['columns'];
    numberInputs.forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('input', (e) => {
          this._updateConfig(id, parseInt(e.target.value) || 3);
        });
      }
    });

    // Select inputs
    const selectInputs = ['thumbnail_size'];
    selectInputs.forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('change', (e) => {
          this._updateConfig(id, parseInt(e.target.value));
        });
      }
    });

    // Checkbox inputs
    const checkboxInputs = ['show_upload', 'show_gallery', 'show_entities'];
    checkboxInputs.forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('change', (e) => {
          this._updateConfig(id, e.target.checked);
        });
      }
    });
  }

  _updateConfig(key, value) {
    this._config = { ...this._config, [key]: value };
    this._updatePreview();
    this._fireConfigChanged();
  }

  _updatePreview() {
    const preview = this.shadowRoot.getElementById('config-preview');
    if (preview) {
      // Create a clean config object for preview
      const cleanConfig = { ...this._config };
      
      // Remove undefined values and set defaults
      if (!cleanConfig.title) cleanConfig.title = 'Image Manager';
      if (cleanConfig.show_upload === undefined) cleanConfig.show_upload = true;
      if (cleanConfig.show_gallery === undefined) cleanConfig.show_gallery = true;
      if (cleanConfig.show_entities === undefined) cleanConfig.show_entities = true;
      if (!cleanConfig.columns) cleanConfig.columns = 3;
      if (!cleanConfig.thumbnail_size) cleanConfig.thumbnail_size = 150;

      let previewText = `type: custom:image-manager-card
title: "${cleanConfig.title}"
show_upload: ${cleanConfig.show_upload}
show_gallery: ${cleanConfig.show_gallery}
show_entities: ${cleanConfig.show_entities}
columns: ${cleanConfig.columns}
thumbnail_size: ${cleanConfig.thumbnail_size}`;

      if (cleanConfig.target_input_text) {
        previewText += `
target_input_text: "${cleanConfig.target_input_text}"`;
      }

      preview.textContent = previewText;
    }
  }

  _fireConfigChanged() {
    const event = new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  static get styles() {
    return [];
  }
}

customElements.define('image-manager-card-editor', ImageManagerCardEditor);

/* Image Manager Selector Card */
class ImageManagerSelectorCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._images = [];
    this._selectedImage = null;
    this._initialized = false;
    this._loadingPromise = null;
    this._lastLoadTime = 0;
  }

  static getStubConfig() {
    return {
      type: 'custom:image-manager-selector-card',
      title: 'Image Selector',
      target_input_text: '',
      target_pdf_input_text: '',
      show_preview: true,
    };
  }

  static getConfigElement() {
    return document.createElement('image-manager-selector-card-editor');
  }

  setConfig(config) {
    if (!config.target_input_text) {
      throw new Error('target_input_text is a required configuration option.');
    }

    this._config = {
      title: 'Image Selector',
      show_preview: true,
      ...config,
    };

    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Only load images if this is the first time hass is set or if explicitly needed
    if (!this._initialized) {
      this._initialized = true;
      this._loadImages();
    }
  }

  async _loadImages() {
    if (!this._hass) return;

    const now = Date.now();
    // Prevent loading more than once every 5 seconds
    if (now - this._lastLoadTime < 5000) {
      return;
    }

    // If already loading, wait for the existing request
    if (this._loadingPromise) {
      return this._loadingPromise;
    }

    this._lastLoadTime = now;
    this._loadingPromise = (async () => {
      try {
        const response = await this._hass.callApi('GET', 'image_manager/status');
        const newImages = response.images || [];

        // Smart loading: only update if there are actual changes
        const currentSequences = new Set(this._images.map(img => img.sequence));
        const newSequences = new Set(newImages.map(img => img.sequence));

        const hasNewImages = newImages.some(img => !currentSequences.has(img.sequence));
        const hasRemovedImages = this._images.some(img => !newSequences.has(img.sequence));

        if (hasNewImages || hasRemovedImages) {
          this._images = newImages;
          // Clear selection if selected image was removed
          if (this._selectedImage && !newSequences.has(this._selectedImage.sequence)) {
            this._selectedImage = null;
          }
          this._render();
        }
      } catch (error) {
        console.error('Failed to load images:', error);
        this.shadowRoot.innerHTML = `<ha-card><div class="card-content">Error loading images.</div></ha-card>`;
      } finally {
        this._loadingPromise = null;
      }
    })();

    return this._loadingPromise;
  }

  _render() {
    if (!this.shadowRoot) return;

    const selectedImageUrl = this._selectedImage ? this._selectedImage.url : '';

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 8px;
        }
        .preview {
          margin-top: 16px;
          text-align: center;
        }
        .preview img {
          max-width: 100%;
          max-height: 300px;
          border-radius: 8px;
        }
        .actions {
          display: flex;
          justify-content: space-between;
          margin-top: 16px;
        }
        .dropdown-container {
          display: flex;
          align-items: center;
          width: 100%;
        }
        ha-select {
          width: 100%;
        }
        .hidden {
          display: none;
        }
      </style>
      <ha-card header="${this._config.title}">
        <div class="card-content">
          <div class="dropdown-container">
            <ha-select label="Select Image" naturalMenuWidth>
              ${this._images.map(image => `
                <mwc-list-item value="${image.sequence}" graphic="avatar">
                  <span>${image.sequence} - ${image.filename}</span>
                  <img slot="graphic" src="${image.url}" />
                </mwc-list-item>
              `).join('')}
            </ha-select>
          </div>
          ${this._config.show_preview ? `
            <div class="preview ${!this._selectedImage ? 'hidden' : ''}">
              <img src="${selectedImageUrl}" />
            </div>
          ` : ''}
          <div class="actions ${!this._selectedImage ? 'hidden' : ''}">
            <mwc-button outlined data-action="view">View</mwc-button>
            <mwc-button raised data-action="set">Set</mwc-button>
          </div>
        </div>
      </ha-card>
    `;

    this._attachEventListeners();
  }

  _attachEventListeners() {
    // Handle select change
    const select = this.shadowRoot.querySelector('ha-select');
    if (select) {
      select.addEventListener('selected', (e) => {
        const sequence = e.target.value;
        this._selectedImage = this._images.find(img => img.sequence == sequence);
        this._render();
      });
    }

    // Handle button clicks
    this.shadowRoot.querySelectorAll('[data-action]').forEach(button => {
      button.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'view') {
          this._handleView();
        } else if (action === 'set') {
          this._handleSet();
        }
      });
    });
  }

  _handleImageSelection(e) {
    const sequence = e.target.value;
    this._selectedImage = this._images.find(img => img.sequence == sequence);
    this._render();
  }

  _handleView() {
    if (this._selectedImage) {
      window.open(this._selectedImage.url, '_blank');
    }
  }

  async _handleSet() {
    if (!this._selectedImage || !this._hass) return;

    try {
      await this._hass.callService('input_text', 'set_value', {
        entity_id: this._config.target_input_text,
        value: this._selectedImage.url,
      });

      if (this._config.target_pdf_input_text && this._selectedImage.pdf_url) {
        await this._hass.callService('input_text', 'set_value', {
          entity_id: this._config.target_pdf_input_text,
          value: this._selectedImage.pdf_url,
        });
      }

      this._showFeedback('Image set successfully!', 'success');
    } catch (error) {
      console.error('Failed to set image:', error);
      this._showFeedback('Failed to set image.', 'error');
    }
  }

  _showFeedback(message, level = 'info') {
    const feedbackElement = document.createElement('div');
    feedbackElement.style.position = 'fixed';
    feedbackElement.style.bottom = '20px';
    feedbackElement.style.left = '50%';
    feedbackElement.style.transform = 'translateX(-50%)';
    feedbackElement.style.padding = '16px';
    feedbackElement.style.borderRadius = '8px';
    feedbackElement.style.color = 'white';
    feedbackElement.style.backgroundColor = level === 'success' ? 'green' : 'red';
    feedbackElement.textContent = message;
    this.shadowRoot.appendChild(feedbackElement);
    setTimeout(() => {
      feedbackElement.remove();
    }, 3000);
  }
}

customElements.define('image-manager-selector-card', ImageManagerSelectorCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'image-manager-selector-card',
  name: 'Image Manager Selector Card',
  preview: true,
  description: 'A card to select an image and set it to an input_text helper.',
});

/* Image Manager Selector Card Editor */
class ImageManagerSelectorEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
  }

  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <div class="card-config">
        <paper-input
          label="Title"
          .value="${this._config.title || ''}"
          .configValue="${'title'}"
          @value-changed="${this._handleConfigChanged}"
        ></paper-input>
        <paper-input
          label="Target Input Text"
          .value="${this._config.target_input_text || ''}"
          .configValue="${'target_input_text'}"
          @value-changed="${this._handleConfigChanged}"
          required
        ></paper-input>
        <paper-input
          label="Target PDF Input Text"
          .value="${this._config.target_pdf_input_text || ''}"
          .configValue="${'target_pdf_input_text'}"
          @value-changed="${this._handleConfigChanged}"
        ></paper-input>
        <ha-formfield label="Show Preview">
          <ha-switch
            .checked="${this._config.show_preview !== false}"
            .configValue="${'show_preview'}"
            @change="${this._handleConfigChanged}"
          ></ha-switch>
        </ha-formfield>
      </div>
    `;
  }

  _handleConfigChanged(e) {
    if (!this._config || !this._hass) {
      return;
    }

    const target = e.target;
    // For ha-switch @change event, use .checked. For paper-input @value-changed, use .value or e.detail.value if available but .value usually works.
    // However, for HA elements, detail.value works best.
    const value = target.checked !== undefined ? target.checked : (e.detail && e.detail.value !== undefined ? e.detail.value : target.value);
    const configValue = target.configValue;

    if (this._config[configValue] !== value) {
      this._config = { ...this._config, [configValue]: value };
      const event = new CustomEvent('config-changed', {
        bubbles: true,
        composed: true,
        detail: { config: this._config },
      });
      this.dispatchEvent(event);
    }
  }
}

customElements.define('image-manager-selector-card-editor', ImageManagerSelectorEditor);
