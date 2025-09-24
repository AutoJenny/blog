/**
 * Blog Input Data Core Module
 * Handles display of blog post sections in collapsible format
 */

class BlogInputDataManager {
    constructor() {
        this.currentPost = null;
        this.currentSections = [];
        this.expandedSections = new Set();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.listenForPostSelection();
    }

    setupEventListeners() {
        // Expand/Collapse controls
        const expandAllBtn = document.getElementById('expand-all-sections');
        const collapseAllBtn = document.getElementById('collapse-all-sections');
        const generateAllBtn = document.getElementById('generate-all-sections');

        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => this.expandAllSections());
        }

        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => this.collapseAllSections());
        }

        if (generateAllBtn) {
            generateAllBtn.addEventListener('click', () => this.generateAllSections());
        }
    }

    listenForPostSelection() {
        document.addEventListener('postSelected', (event) => {
            const { post, sections } = event.detail;
            if (post && sections) {
                this.updateBlogData(post, sections);
            }
        });
    }

    updateBlogData(post, sections) {
        this.currentPost = post;
        this.currentSections = sections;

        // Update status
        const statusElement = document.getElementById('input-data-status');
        if (statusElement) {
            statusElement.textContent = `${post.title} (${sections.length} sections)`;
        }

        // Show blog sections display
        const blogDisplay = document.getElementById('blog-sections-display');
        if (blogDisplay) {
            blogDisplay.classList.remove('d-none');
        }

        // Hide waiting message
        const waitingDisplay = document.getElementById('input-data-display');
        if (waitingDisplay) {
            waitingDisplay.style.display = 'none';
        }

        // Update blog post header
        this.updateBlogPostHeader(post);

        // Render sections
        this.renderSections(sections);

        // Update summary
        this.updateSectionsSummary();
    }

    updateBlogPostHeader(post) {
        const elements = {
            'blog-post-title': post.title,
            'blog-post-id': post.id,
            'blog-post-url': this.constructPostUrl(post.slug),
            'blog-sections-count': this.currentSections.length,
            'blog-post-status': post.status
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    constructPostUrl(slug) {
        return `https://clan.com/blog/${slug}`;
    }

    renderSections(sections) {
        const container = document.getElementById('sections-container');
        if (!container) return;

        container.innerHTML = '';

        sections.forEach((section, index) => {
            const sectionElement = this.createSectionElement(section, index);
            container.appendChild(sectionElement);
        });
    }

    createSectionElement(section, index) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'blog-section-item mb-3 border border-secondary rounded';
        sectionDiv.id = `section-${section.id}`;

        const isExpanded = this.expandedSections.has(section.id);
        const contentDisplay = isExpanded ? 'block' : 'none';

        sectionDiv.innerHTML = `
            <div class="section-header p-3 bg-dark cursor-pointer" onclick="blogInputDataManager.toggleSection(${section.id})">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'} me-2 text-primary"></i>
                        <div>
                            <h6 class="text-white mb-1">Section ${section.section_order}: ${section.section_heading}</h6>
                            <small class="text-muted">ID: ${section.id} | Order: ${section.section_order}</small>
                        </div>
                    </div>
                    <div class="d-flex align-items-center">
                        <span class="badge bg-info me-2">${index + 1}/${this.currentSections.length}</span>
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); blogInputDataManager.generateSection(${section.id})">
                            <i class="fas fa-magic me-1"></i>Generate
                        </button>
                    </div>
                </div>
            </div>
            <div class="section-content p-3" style="display: ${contentDisplay};">
                <div class="row">
                    <div class="col-md-3">
                        <div class="section-image">
                            <img src="${this.constructImageUrl(section)}" 
                                 class="img-thumbnail" 
                                 style="width: 120px; height: 90px; object-fit: cover;"
                                 alt="Section illustration"
                                 onerror="this.style.display='none'">
                        </div>
                    </div>
                    <div class="col-md-9">
                        <div class="section-details">
                            <h6 class="text-light mb-2">Content:</h6>
                            <div class="content-preview" style="max-height: 200px; overflow-y: auto; background: #1e293b; padding: 10px; border-radius: 4px; font-size: 0.85rem;">
                                ${this.stripHtml(section.polished || section.section_description || 'No content available')}
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <strong>Image:</strong> ${section.image_filename || 'None'}<br>
                                    <strong>Description:</strong> ${section.section_description || 'None'}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return sectionDiv;
    }

    constructImageUrl(section) {
        if (!section.image_filename) return '';
        
        // Use the same logic as the post section selection
        let filename;
        if (section.image_filename.includes('d59ac061-0b2a-4a06-a3a6-c15d13dc35e2')) {
            filename = section.image_filename.endsWith('_processed.png') ? 
                section.image_filename : 
                section.image_filename.replace('.png', '_processed.png');
        } else if (section.id === 711 && (section.image_filename.includes('live_preview_content') || section.image_filename.includes('generated_image'))) {
            filename = 'generated_image_20250727_145859_processed.png';
        } else {
            filename = `${section.id}_processed.png`;
        }
        
        return `/static/images/content/posts/${this.currentPost.id}/sections/${section.id}/optimized/${filename}`;
    }

    stripHtml(html) {
        if (!html) return '';
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    }

    toggleSection(sectionId) {
        const sectionElement = document.getElementById(`section-${sectionId}`);
        if (!sectionElement) return;

        const contentDiv = sectionElement.querySelector('.section-content');
        const chevronIcon = sectionElement.querySelector('.fa-chevron-right, .fa-chevron-down');
        
        if (!contentDiv || !chevronIcon) return;

        const isExpanded = contentDiv.style.display === 'block';
        
        if (isExpanded) {
            contentDiv.style.display = 'none';
            chevronIcon.className = 'fas fa-chevron-right me-2 text-primary';
            this.expandedSections.delete(sectionId);
        } else {
            contentDiv.style.display = 'block';
            chevronIcon.className = 'fas fa-chevron-down me-2 text-primary';
            this.expandedSections.add(sectionId);
        }
    }

    expandAllSections() {
        this.currentSections.forEach(section => {
            this.expandedSections.add(section.id);
        });
        this.renderSections(this.currentSections);
    }

    collapseAllSections() {
        this.expandedSections.clear();
        this.renderSections(this.currentSections);
    }

    generateSection(sectionId) {
        const section = this.currentSections.find(s => s.id === sectionId);
        if (!section) return;

        // Create data package for this section
        const dataPackage = this.createSectionDataPackage(section);
        
        // Dispatch event for AI content generation
        const event = new CustomEvent('dataSelected', {
            detail: { dataPackage: dataPackage }
        });
        document.dispatchEvent(event);

        console.log('Generating content for section:', section.section_heading);
    }

    generateAllSections() {
        if (!this.currentSections.length) return;

        // Create data package for all sections
        const dataPackage = this.createAllSectionsDataPackage();
        
        // Dispatch event for AI content generation
        const event = new CustomEvent('dataSelected', {
            detail: { dataPackage: dataPackage }
        });
        document.dispatchEvent(event);

        console.log('Generating content for all sections');
    }

    createSectionDataPackage(section) {
        return {
            data_type: 'blog_section',
            platform: { name: 'facebook', display_name: 'Facebook' },
            channel_type: { name: 'blog_post', display_name: 'Blog Posts' },
            source_data: {
                // Post Information
                post_id: this.currentPost.id,
                post_title: this.currentPost.title,
                post_slug: this.currentPost.slug,
                post_url: this.constructPostUrl(this.currentPost.slug),
                
                // Section Information
                section_id: section.id,
                section_title: section.section_heading,
                section_content: section.polished,
                section_image_filename: section.image_filename,
                section_image_url: this.constructImageUrl(section),
                section_order: section.section_order,
                section_description: section.section_description,
                
                // Additional Context
                total_sections: this.currentSections.length,
                current_section: section.section_order
            },
            generation_config: {
                content_types: ['feature', 'benefit', 'story'],
                max_length: 280,
                include_hashtags: true,
                include_url: true,
                include_image: true
            },
            timestamp: new Date().toISOString()
        };
    }

    createAllSectionsDataPackage() {
        return {
            data_type: 'blog_sections',
            platform: { name: 'facebook', display_name: 'Facebook' },
            channel_type: { name: 'blog_post', display_name: 'Blog Posts' },
            source_data: {
                // Post Information
                post_id: this.currentPost.id,
                post_title: this.currentPost.title,
                post_slug: this.currentPost.slug,
                post_url: this.constructPostUrl(this.currentPost.slug),
                
                // All Sections
                sections: this.currentSections.map(section => ({
                    section_id: section.id,
                    section_title: section.section_heading,
                    section_content: section.polished,
                    section_image_filename: section.image_filename,
                    section_image_url: this.constructImageUrl(section),
                    section_order: section.section_order,
                    section_description: section.section_description
                })),
                
                // Additional Context
                total_sections: this.currentSections.length
            },
            generation_config: {
                content_types: ['feature', 'benefit', 'story'],
                max_length: 280,
                include_hashtags: true,
                include_url: true,
                include_image: true
            },
            timestamp: new Date().toISOString()
        };
    }

    updateSectionsSummary() {
        const summaryElement = document.getElementById('sections-summary');
        if (summaryElement) {
            const expandedCount = this.expandedSections.size;
            summaryElement.textContent = `${this.currentSections.length} sections loaded (${expandedCount} expanded)`;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogInputDataManager = new BlogInputDataManager();
});
