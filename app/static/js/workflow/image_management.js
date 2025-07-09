/**
 * Image Management Module
 * Handles all image-related functionality in the workflow
 */

class ImageManagement {
    constructor(postId, sectionId = null) {
        console.log('ImageManagement constructor called with postId:', postId, 'sectionId:', sectionId);
        this.postId = postId;
        this.sectionId = sectionId;
        this.currentImage = null;
        this.imageSettings = [];
        this.imageStyles = [];
        this.imageFormats = [];
        this.sectionImages = [];
        
        this.init();
    }

    async init() {
        console.log('ImageManagement init started');
        try {
            console.log('Setting up tabs...');
            this.setupTabs();
            console.log('Setting up upload...');
            this.setupUpload();
            console.log('Loading image settings...');
            await this.loadImageSettings();
            console.log('Loading image styles...');
            await this.loadImageStyles();
            console.log('Loading image formats...');
            await this.loadImageFormats();
            console.log('Loading sections dropdown...');
            await this.loadSectionsDropdown();
            console.log('Binding events...');
            this.bindEvents();
            console.log('Updating status...');
            this.updateStatus('Ready');
            console.log('ImageManagement init completed successfully');
        } catch (error) {
            console.error('Failed to initialize image management:', error);
            this.updateStatus('Error', 'error');
        }
    }

    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                tabContents.forEach(tc => tc.style.display = 'none');
                document.getElementById('tab-' + btn.dataset.tab).style.display = 'block';
            });
        });
    }

    setupUpload() {
        const uploadArea = document.getElementById('upload-area');
        const uploadInput = document.getElementById('image-upload-input');
        const uploadPreview = document.getElementById('upload-preview');
        const uploadPreviewImg = document.getElementById('upload-preview-img');
        const confirmUploadBtn = document.getElementById('confirm-upload-btn');
        if (!uploadArea || !uploadInput || !uploadPreview || !uploadPreviewImg || !confirmUploadBtn) return;
        // Drag & drop
        uploadArea.addEventListener('dragover', e => {
            e.preventDefault();
            uploadArea.style.background = '#1a365d';
        });
        uploadArea.addEventListener('dragleave', e => {
            e.preventDefault();
            uploadArea.style.background = '#23273a';
        });
        uploadArea.addEventListener('drop', e => {
            e.preventDefault();
            uploadArea.style.background = '#23273a';
            const file = e.dataTransfer.files[0];
            if (file) this.previewUpload(file);
        });
        // File input
        uploadArea.addEventListener('click', () => uploadInput.click());
        uploadInput.addEventListener('change', e => {
            const file = e.target.files[0];
            if (file) this.previewUpload(file);
        });
        // Confirm upload
        confirmUploadBtn.addEventListener('click', () => {
            if (this.uploadFile) this.uploadImageToSection(this.uploadFile);
        });
    }

    previewUpload(file) {
        const uploadPreview = document.getElementById('upload-preview');
        const uploadPreviewImg = document.getElementById('upload-preview-img');
        if (!uploadPreview || !uploadPreviewImg) return;
        const reader = new FileReader();
        reader.onload = e => {
            uploadPreviewImg.src = e.target.result;
            uploadPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
        this.uploadFile = file;
    }

    async uploadImageToSection(file) {
        if (!this.sectionId) {
            alert('No section selected.');
            return;
        }
        const formData = new FormData();
        formData.append('image', file);
        formData.append('section_id', this.sectionId);
        formData.append('post_id', this.postId);
        try {
            const response = await fetch(`/api/images/upload`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error('Upload failed');
            this.updateStatus('Image uploaded');
            document.getElementById('upload-preview').style.display = 'none';
            await this.loadSectionImages();
        } catch (error) {
            this.updateStatus('Upload error', 'error');
            alert('Image upload failed: ' + error.message);
        }
    }

    async loadImageSettings() {
        try {
            const response = await fetch('/api/images/settings');
            if (!response.ok) throw new Error('Failed to load image settings');
            this.imageSettings = await response.json();
            this.populateSettingsDropdown();
        } catch (error) {
            console.error('Error loading image settings:', error);
            this.updateStatus('Settings Error', 'error');
        }
    }

    async loadImageStyles() {
        try {
            const response = await fetch('/api/images/styles');
            if (!response.ok) throw new Error('Failed to load image styles');
            this.imageStyles = await response.json();
            this.populateStylesDropdown();
        } catch (error) {
            console.error('Error loading image styles:', error);
            this.updateStatus('Styles Error', 'error');
        }
    }

    async loadImageFormats() {
        try {
            const response = await fetch('/api/images/formats');
            if (!response.ok) throw new Error('Failed to load image formats');
            this.imageFormats = await response.json();
            this.populateFormatsDropdown();
        } catch (error) {
            console.error('Error loading image formats:', error);
            this.updateStatus('Formats Error', 'error');
        }
    }

    async loadSectionsDropdown() {
        // Fetch all sections for the current post
        const dropdown = document.getElementById('section-select');
        if (!dropdown) {
            console.error('Section dropdown not found');
            return;
        }
        console.log('Loading sections dropdown for post:', this.postId);
        try {
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections`);
            console.log('API response status:', response.status);
            if (!response.ok) throw new Error('Failed to fetch sections');
            const data = await response.json();
            console.log('Sections data:', data);
            this.sections = data.sections || [];
            console.log('Processed sections:', this.sections);
            dropdown.innerHTML = '';
            this.sections.forEach(section => {
                const opt = document.createElement('option');
                opt.value = section.id;
                opt.textContent = section.title || `Section ${section.id}`;
                dropdown.appendChild(opt);
            });
            // Auto-select first section if available
            if (this.sections.length > 0) {
                dropdown.value = this.sections[0].id;
                this.setSectionId(this.sections[0].id);
            }
            dropdown.addEventListener('change', (e) => {
                this.setSectionId(e.target.value);
            });
        } catch (error) {
            console.error('Error loading sections dropdown:', error);
            dropdown.innerHTML = '<option value="">Error loading sections</option>';
        }
    }

    async loadSectionImages() {
        if (!this.sectionId) return;
        
        try {
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections/${this.sectionId}`);
            if (!response.ok) throw new Error('Failed to load section data');
            const sectionData = await response.json();
            
            this.updateSectionStatus(sectionData);
            this.loadSectionImagesFromData(sectionData);
        } catch (error) {
            console.error('Error loading section images:', error);
        }
    }

    updateSectionStatus(sectionData) {
        const currentSectionName = document.getElementById('current-section-name');
        const imagesGeneratedCount = document.getElementById('images-generated-count');
        const lastGeneratedTime = document.getElementById('last-generated-time');

        if (currentSectionName) {
            currentSectionName.textContent = sectionData.title || 'Unknown Section';
        }

        if (imagesGeneratedCount) {
            const imageCount = sectionData.generated_image_url ? 1 : 0;
            imagesGeneratedCount.textContent = imageCount;
        }

        if (lastGeneratedTime) {
            const lastGenerated = sectionData.image_generation_metadata?.generated_at || 'Never';
            lastGeneratedTime.textContent = lastGenerated;
        }
    }

    loadSectionImagesFromData(sectionData) {
        const imageGrid = document.getElementById('image-grid');
        const noImagesMessage = document.getElementById('no-images-message');

        if (!imageGrid || !noImagesMessage) return;

        if (sectionData.generated_image_url) {
            // Show image grid
            noImagesMessage.style.display = 'none';
            imageGrid.style.display = 'grid';
            
            // Clear existing images
            imageGrid.innerHTML = '';
            
            // Add the generated image
            const imageItem = this.createImageItem(sectionData.generated_image_url, sectionData);
            imageGrid.appendChild(imageItem);
        } else {
            // Show no images message
            noImagesMessage.style.display = 'block';
            imageGrid.style.display = 'none';
        }
    }

    createImageItem(imageUrl, metadata = {}) {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.dataset.imageUrl = imageUrl;
        imageItem.dataset.metadata = JSON.stringify(metadata);

        imageItem.innerHTML = `
            <img src="${imageUrl}" alt="Generated Image" onerror="this.style.display='none'">
            <div class="image-overlay">
                <i class="fas fa-eye"></i>
            </div>
        `;

        imageItem.addEventListener('click', () => this.selectImage(imageItem, metadata));
        return imageItem;
    }

    selectImage(imageItem, metadata) {
        // Remove previous selection
        document.querySelectorAll('.image-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Add selection to current item
        imageItem.classList.add('selected');

        // Update metadata display
        this.updateImageMetadata(metadata);

        // Enable action buttons
        this.enableActionButtons();

        // Store current image
        this.currentImage = {
            url: imageItem.dataset.imageUrl,
            metadata: metadata
        };
    }

    updateImageMetadata(metadata) {
        const imagePrompt = document.getElementById('image-prompt');
        const imageStyle = document.getElementById('image-style');
        const imageGeneratedTime = document.getElementById('image-generated-time');
        const imageSize = document.getElementById('image-size');

        if (imagePrompt) {
            imagePrompt.textContent = metadata.image_prompts || 'No prompt available';
        }

        if (imageStyle) {
            imageStyle.textContent = metadata.image_style || '-';
        }

        if (imageGeneratedTime) {
            imageGeneratedTime.textContent = metadata.generated_at || '-';
        }

        if (imageSize) {
            imageSize.textContent = metadata.image_size || '-';
        }
    }

    enableActionButtons() {
        const buttons = [
            'optimize-image-btn',
            'watermark-image-btn', 
            'download-image-btn',
            'delete-image-btn'
        ];

        buttons.forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) btn.disabled = false;
        });
    }

    populateSettingsDropdown() {
        const dropdown = document.getElementById('image-settings');
        if (!dropdown) return;
        
        dropdown.innerHTML = '';
        
        if (this.imageSettings.length === 0) {
            // Add a default option if no settings exist
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = 'No settings available';
            dropdown.appendChild(defaultOpt);
        } else {
            this.imageSettings.forEach(setting => {
                const opt = document.createElement('option');
                opt.value = setting.id;
                opt.textContent = setting.name;
                dropdown.appendChild(opt);
            });
        }
    }

    populateStylesDropdown() {
        const dropdown = document.getElementById('image-settings');
        if (!dropdown) return;
        
        dropdown.innerHTML = '';
        
        if (this.imageStyles.length === 0) {
            // Add default options if no styles exist
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = 'Default Style';
            dropdown.appendChild(defaultOpt);
        } else {
            this.imageStyles.forEach(style => {
                const opt = document.createElement('option');
                opt.value = style.id;
                opt.textContent = style.title;
                dropdown.appendChild(opt);
            });
        }
    }

    populateFormatsDropdown() {
        const dropdown = document.getElementById('image-format');
        if (!dropdown) return;
        
        dropdown.innerHTML = '';
        
        if (this.imageFormats.length === 0) {
            // Add default options if no formats exist
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = 'Default (512x512)';
            dropdown.appendChild(defaultOpt);
        } else {
            this.imageFormats.forEach(format => {
                const opt = document.createElement('option');
                opt.value = format.id;
                opt.textContent = format.title;
                dropdown.appendChild(opt);
            });
        }
    }

    bindEvents() {
        // Generate image button
        const generateBtn = document.getElementById('generate-image-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateImage());
        }

        // Generate prompt button
        const promptBtn = document.getElementById('generate-prompt-btn');
        if (promptBtn) {
            promptBtn.addEventListener('click', () => this.generatePrompt());
        }

        // Action buttons
        const optimizeBtn = document.getElementById('optimize-image-btn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizeImage());
        }

        const watermarkBtn = document.getElementById('watermark-image-btn');
        if (watermarkBtn) {
            watermarkBtn.addEventListener('click', () => this.watermarkImage());
        }

        const downloadBtn = document.getElementById('download-image-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadImage());
        }

        const deleteBtn = document.getElementById('delete-image-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deleteImage());
        }

        // Modal download button
        const modalDownloadBtn = document.getElementById('modal-download-btn');
        if (modalDownloadBtn) {
            modalDownloadBtn.addEventListener('click', () => this.downloadImage());
        }
    }

    async generateImage() {
        if (!this.sectionId) {
            alert('Please select a section first');
            return;
        }

        const provider = document.getElementById('image-provider')?.value;
        const style = document.getElementById('image-settings')?.value;
        const format = document.getElementById('image-format')?.value;

        if (!provider || !style) {
            alert('Please select a provider and style');
            return;
        }

        this.showLoading('Generating image...');

        try {
            const response = await fetch('/api/images/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: provider,
                    style_id: style,
                    format_id: format,
                    section_id: this.sectionId,
                    post_id: this.postId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate image');
            }

            const result = await response.json();
            await this.updateSectionWithImage(result);
            this.updateStatus('Image generated successfully', 'success');

        } catch (error) {
            console.error('Error generating image:', error);
            this.updateStatus('Generation failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async generatePrompt() {
        if (!this.sectionId) {
            alert('Please select a section first');
            return;
        }

        this.showLoading('Generating prompt...');

        try {
            // This would integrate with the LLM workflow to generate image prompts
            // For now, we'll use a placeholder
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections/${this.sectionId}/generate_prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error('Failed to generate prompt');
            }

            const result = await response.json();
            this.updateStatus('Prompt generated successfully', 'success');

        } catch (error) {
            console.error('Error generating prompt:', error);
            this.updateStatus('Prompt generation failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async updateSectionWithImage(imageData) {
        try {
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections/${this.sectionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    generated_image_url: imageData.image_url,
                    image_generation_metadata: imageData.metadata,
                    image_prompts: imageData.prompt
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update section with image');
            }

            // Reload section images
            await this.loadSectionImages();

        } catch (error) {
            console.error('Error updating section with image:', error);
            throw error;
        }
    }

    async optimizeImage() {
        if (!this.currentImage) {
            alert('Please select an image first');
            return;
        }

        this.showLoading('Optimizing image...');

        try {
            const response = await fetch('/api/images/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_url: this.currentImage.url
                })
            });

            if (!response.ok) {
                throw new Error('Failed to optimize image');
            }

            const result = await response.json();
            this.updateStatus('Image optimized successfully', 'success');

        } catch (error) {
            console.error('Error optimizing image:', error);
            this.updateStatus('Optimization failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async watermarkImage() {
        if (!this.currentImage) {
            alert('Please select an image first');
            return;
        }

        this.showLoading('Adding watermark...');

        try {
            const response = await fetch('/api/images/watermark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_url: this.currentImage.url
                })
            });

            if (!response.ok) {
                throw new Error('Failed to add watermark');
            }

            const result = await response.json();
            this.updateStatus('Watermark added successfully', 'success');

        } catch (error) {
            console.error('Error adding watermark:', error);
            this.updateStatus('Watermark failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    downloadImage() {
        if (!this.currentImage) {
            alert('Please select an image first');
            return;
        }

        const link = document.createElement('a');
        link.href = this.currentImage.url;
        link.download = `image_${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async deleteImage() {
        if (!this.currentImage) {
            alert('Please select an image first');
            return;
        }

        if (!confirm('Are you sure you want to delete this image?')) {
            return;
        }

        this.showLoading('Deleting image...');

        try {
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections/${this.sectionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    generated_image_url: null,
                    image_generation_metadata: null,
                    image_prompts: null
                })
            });

            if (!response.ok) {
                throw new Error('Failed to delete image');
            }

            this.currentImage = null;
            await this.loadSectionImages();
            this.updateStatus('Image deleted successfully', 'success');

        } catch (error) {
            console.error('Error deleting image:', error);
            this.updateStatus('Deletion failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    updateStatus(message, type = 'info') {
        const statusIndicator = document.getElementById('image-status-indicator');
        if (!statusIndicator) return;

        statusIndicator.textContent = message;
        statusIndicator.className = `status-indicator status-${type}`;
    }

    showLoading(message) {
        const overlay = document.getElementById('image-loading-overlay');
        const loadingMessage = document.getElementById('loading-message');
        
        if (overlay) overlay.style.display = 'flex';
        if (loadingMessage) loadingMessage.textContent = message;
    }

    hideLoading() {
        const overlay = document.getElementById('image-loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    setSectionId(sectionId) {
        this.sectionId = sectionId;
        const currentSectionIdElem = document.getElementById('current-section-id');
        if (currentSectionIdElem) {
            currentSectionIdElem.textContent = `(#${sectionId})`;
        }
        this.loadSectionImages();
    }
}

// Export for use in other modules
export default ImageManagement; 