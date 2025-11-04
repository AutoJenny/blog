/**
 * Imaging Sections Panel - Imaging-specific batch selection and generation
 * - Toggle Select/Unselect All affects checkboxes only (batch set)
 * - Highlighted row controls preview; independent from checkbox selection
 * - "Generate Selected" processes checked sections sequentially via imaging API
 * - Persists checkbox selection per post in localStorage
 */

class ImagingSectionsPanel {
    constructor(options = {}) {
        this.postId = options.postId || window.postId;
        this.containerId = options.containerId || 'sections-panel';
        this.currentSectionId = null;
        this.sections = [];
        this.selectedSections = new Set();
        this.storageKey = `imaging_selected_sections_${this.postId}`;

        this.callbacks = {
            onSectionSelect: options.onSectionSelect || (() => {}),
            onBatchStart: options.onBatchStart || (() => {}),
            onBatchProgress: options.onBatchProgress || (() => {}),
            onBatchComplete: options.onBatchComplete || (() => {}),
            onSectionUpdate: options.onSectionUpdate || (() => {})
        };

        this.init();
    }

    init() {
        // Ensure button labels are imaging-appropriate
        const batchBtn = document.getElementById('batch-generate-btn');
        if (batchBtn) batchBtn.textContent = 'Generate Selected';

        this.loadSections();
        this.bindEvents();
    }

    async loadSections() {
        try {
            const response = await fetch(`/imaging/api/posts/${this.postId}/sections`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Failed to load sections');

            // Normalize shape similar to authoring
            this.sections = (data.sections || []).map(section => ({
                id: section.id,
                title: section.section_heading || `Section ${section.id}`,
                subtitle: section.section_description || '',
                order: section.section_order || section.id,
                status: section.status || 'draft',
                ...section
            }));

            this.renderSections();
            const hadSaved = this.restoreSelection();

            // If no saved selection, optionally auto-select all (first load) or when forced via flags
            const urlParams = new URLSearchParams(window.location.search);
            const autoParam = urlParams.get('auto');
            const forceAuto = (typeof window.autoSelectAll !== 'undefined' && window.autoSelectAll === true) || (autoParam === '1' || autoParam === 'true');
            if (!hadSaved || this.selectedSections.size === 0 || forceAuto) {
                this.selectAllInternal(true);
                this.persistSelection();
            }

            this.updateSelectAllToggleLabel();

            // Auto-highlight first section for preview if none highlighted
            if (this.sections.length > 0) {
                this.selectSection(this.sections[0].id);
            }
        } catch (err) {
            console.error('[ImagingSectionsPanel] Error loading sections:', err);
        }
    }

    renderSections() {
        const container = document.getElementById('sections-list');
        if (!container) return;
        container.innerHTML = '';

        this.sections.forEach(section => {
            const div = document.createElement('div');
            div.className = 'section-item';
            div.dataset.sectionId = section.id;
            div.dataset.status = section.status || 'draft';

            div.innerHTML = `
                <div class="section-header">
                    <input type="checkbox" class="section-checkbox" data-section-id="${section.id}">
                    <span class="section-number">${section.order}</span>
                    <span class="section-title">${section.title}</span>
                    <span class="section-status ${section.status || 'draft'}">${(section.status || 'draft').replace(/^./, c => c.toUpperCase())}</span>
                </div>
                <div class="section-subtitle">${section.subtitle || ''}</div>
            `;

            // Row click highlights for preview only
            div.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    this.selectSection(section.id);
                }
            });

            // Checkbox controls batch selection set
            const checkbox = div.querySelector('.section-checkbox');
            checkbox.addEventListener('change', (e) => {
                const id = checkbox.dataset.sectionId;
                if (e.target.checked) this.selectedSections.add(id);
                else this.selectedSections.delete(id);
                this.persistSelection();
                this.updateSelectAllToggleLabel();
                this.updateGenerateButtonState();
            });

            container.appendChild(div);
        });

        // Ensure generate button state reflects current UI after render
        this.updateGenerateButtonState();
    }

    selectSection(sectionId) {
        this.currentSectionId = sectionId;
        document.querySelectorAll('.section-item').forEach(item => item.classList.remove('selected'));
        const currentItem = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (currentItem) currentItem.classList.add('selected');

        const section = this.sections.find(s => s.id === sectionId);
        if (section) this.callbacks.onSectionSelect({ sectionId, section, postId: this.postId });
    }

    bindEvents() {
        // Toggle Select/Unselect All
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.toggleSelectAll());
        }

        // Generate Selected
        const batchGenerateBtn = document.getElementById('batch-generate-btn');
        if (batchGenerateBtn) {
            batchGenerateBtn.addEventListener('click', () => this.batchGenerateSelected());
        }

        // Defensive: container-level change listener to catch any checkbox changes
        const container = document.getElementById('sections-list');
        if (container) {
            container.addEventListener('change', (e) => {
                const target = e.target;
                if (target && target.classList && target.classList.contains('section-checkbox')) {
                    const id = target.dataset.sectionId;
                    if (target.checked) this.selectedSections.add(id);
                    else this.selectedSections.delete(id);
                    this.persistSelection();
                    this.updateSelectAllToggleLabel();
                    this.updateGenerateButtonState();
                }
            });
        }

        // Listen for image generation events
        document.addEventListener('imageGenerated', (event) => {
            const { sectionId, success } = event.detail;
            if (sectionId) {
                if (success) {
                    this.updateSectionStatus(sectionId, 'complete');
                } else {
                    this.updateSectionStatus(sectionId, 'error');
                }
            }
        });
    }

    toggleSelectAll() {
        const checkboxes = Array.from(document.querySelectorAll('.section-checkbox'));
        const anyChecked = checkboxes.some(cb => cb.checked);
        const newState = !anyChecked; // if any checked, unselect all; else select all

        this.selectAllInternal(newState);

        this.persistSelection();
        this.updateSelectAllToggleLabel();
        this.updateGenerateButtonState();
    }

    // Helper to set all checkbox states and selected set together
    selectAllInternal(state) {
        document.querySelectorAll('.section-checkbox').forEach(cb => {
            cb.checked = state;
            const id = cb.dataset.sectionId;
            if (state) this.selectedSections.add(id);
            else this.selectedSections.delete(id);
        });
    }

    updateSelectAllToggleLabel() {
        const btn = document.getElementById('select-all-btn');
        if (!btn) return;
        const checkboxes = Array.from(document.querySelectorAll('.section-checkbox'));
        const anyChecked = checkboxes.some(cb => cb.checked);
        btn.textContent = anyChecked ? 'Unselect All' : 'Select All';
    }

    updateGenerateButtonState() {
        const btn = document.getElementById('batch-generate-btn');
        if (!btn) return;
        // Prefer actual checkbox state so UI always reflects visible checks
        const anyChecked = Array.from(document.querySelectorAll('.section-checkbox')).some(cb => cb.checked);
        const hasAny = anyChecked || this.selectedSections.size > 0;
        btn.disabled = !hasAny;
        btn.title = hasAny ? '' : 'Select one or more sections first';
    }

    persistSelection() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(Array.from(this.selectedSections)));
        } catch (_) { /* ignore */ }
    }

    restoreSelection() {
        try {
            const raw = localStorage.getItem(this.storageKey);
            const saved = raw ? JSON.parse(raw) : [];
            const ids = new Set(saved);
            document.querySelectorAll('.section-checkbox').forEach(cb => {
                const id = cb.dataset.sectionId;
                cb.checked = ids.has(id);
                if (cb.checked) this.selectedSections.add(id);
                else this.selectedSections.delete(id);
            });
            this.updateGenerateButtonState();
            return !!raw && Array.isArray(saved);
        } catch (_) { /* ignore */ }
        this.updateGenerateButtonState();
        return false;
    }

    async batchGenerateSelected() {
        const selectedIds = Array.from(this.selectedSections);
        if (selectedIds.length === 0) return;

        const btn = document.getElementById('batch-generate-btn');
        const original = btn ? btn.textContent : '';
        if (btn) { btn.disabled = true; btn.textContent = 'Generating...'; }

        this.callbacks.onBatchStart(selectedIds);

        try {
            for (let i = 0; i < selectedIds.length; i++) {
                const sectionId = selectedIds[i];
                const section = this.sections.find(s => s.id === sectionId);
                const sectionTitle = section ? (section.section_heading || section.title || `Section ${sectionId}`) : `Section ${sectionId}`;

                this.callbacks.onBatchProgress({ current: i + 1, total: selectedIds.length, sectionId, sectionTitle, status: 'generating' });

                // Obtain prompt for this specific section
                let image_prompt = '';
                // 1) If prompt panel is showing this section's prompt, use it
                const panel = document.querySelector(`[data-section-id="${sectionId}"] .prompt-text`);
                if (panel && panel.textContent.trim()) {
                    image_prompt = panel.textContent.trim();
                }
                // 2) Fallback to cached sectionsData if available
                if (!image_prompt && window.sectionsData) {
                    const s = window.sectionsData.find(x => String(x.id) === String(sectionId));
                    if (s && s.image_prompts) {
                        if (typeof s.image_prompts === 'object') image_prompt = s.image_prompts.image_prompt || '';
                        else {
                            try { image_prompt = (JSON.parse(s.image_prompts).image_prompt) || s.image_prompts; } catch { image_prompt = s.image_prompts; }
                        }
                    }
                }
                // 3) Final fallback: fetch sections and extract prompt for this id
                if (!image_prompt) {
                    try {
                        const resp = await fetch(`/imaging/api/posts/${this.postId}/sections`);
                        const data = await resp.json();
                        if (data.success && Array.isArray(data.sections)) {
                            const s = data.sections.find(x => String(x.id) === String(sectionId));
                            if (s && s.image_prompts) {
                                if (typeof s.image_prompts === 'object') image_prompt = s.image_prompts.image_prompt || '';
                                else {
                                    try { image_prompt = (JSON.parse(s.image_prompts).image_prompt) || s.image_prompts; } catch { image_prompt = s.image_prompts; }
                                }
                            }
                        }
                    } catch(_) { /* ignore */ }
                }

                // Use different API based on current substage
                let resp;
                let data;
                
                if (window.currentSubstage === 'optimise') {
                    // On optimize page, call optimization API
                    const optParams = {
                        quality: 50,
                        overlay_text: 'AI-generated image',
                        watermark: true,
                        text_overlay: true
                    };
                    resp = await fetch(`/imaging/api/optimize/posts/${this.postId}/sections/${sectionId}/optimize-image`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(optParams)
                    });
                    data = await resp.json();
                } else if (window.currentSubstage === 'photo-selection') {
                    // On photo-selection page (Photo-harvesting route), search and auto-select photos
                    if (!image_prompt) {
                        this.callbacks.onBatchProgress({ current: i + 1, total: selectedIds.length, sectionId, sectionTitle, status: 'error', error: 'No search term found for section' });
                        continue;
                    }
                    
                    // Step 1: Search photos using the search term
                    // Get year/week from URL or window context for week persistence
                    const urlParams = new URLSearchParams(window.location.search);
                    const year = urlParams.get('year') || (window.year && window.year);
                    const week = urlParams.get('week') || (window.week && window.week);
                    
                    let searchUrl = `/imaging/api/photo-search/posts/${this.postId}/sections/${sectionId}/search`;
                    if (year && week) {
                        searchUrl += `?year=${year}&week=${week}`;
                    }
                    
                    const searchParams = {
                        search_term: image_prompt,
                        provider: 'both', // Default to both providers
                        per_page: 20
                    };
                    
                    const searchResp = await fetch(searchUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(searchParams)
                    });
                    
                    const searchData = await searchResp.json();
                    if (!searchData.success || !searchData.results || searchData.results.length === 0) {
                        this.callbacks.onBatchProgress({ current: i + 1, total: selectedIds.length, sectionId, sectionTitle, status: 'error', error: searchData.error || 'No photos found' });
                        continue;
                    }
                    
                    // Step 2: Separate results by orientation
                    const landscapePhotos = [];
                    const portraitPhotos = [];
                    
                    searchData.results.forEach(photo => {
                        const width = photo.width || 0;
                        const height = photo.height || 0;
                        if (width >= height) {
                            landscapePhotos.push(photo);
                        } else {
                            portraitPhotos.push(photo);
                        }
                    });
                    
                    // Step 3: Auto-select first landscape and portrait
                    let landscapeSelected = false;
                    let portraitSelected = false;
                    
                    // Build select URLs with week context if available
                    let selectUrlBase = `/imaging/api/photo-search/posts/${this.postId}/sections/${sectionId}/select`;
                    if (year && week) {
                        selectUrlBase += `?year=${year}&week=${week}`;
                    }
                    
                    if (landscapePhotos.length > 0) {
                        const landscapeSelectResp = await fetch(selectUrlBase, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                provider: landscapePhotos[0].provider,
                                image_id: landscapePhotos[0].image_id,
                                orientation: 'landscape'
                            })
                        });
                        const landscapeSelectData = await landscapeSelectResp.json();
                        landscapeSelected = landscapeSelectData.success;
                    }
                    
                    if (portraitPhotos.length > 0) {
                        const portraitSelectResp = await fetch(selectUrlBase, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                provider: portraitPhotos[0].provider,
                                image_id: portraitPhotos[0].image_id,
                                orientation: 'portrait'
                            })
                        });
                        const portraitSelectData = await portraitSelectResp.json();
                        portraitSelected = portraitSelectData.success;
                    }
                    
                    if (landscapeSelected || portraitSelected) {
                        data = { success: true, selected_landscape: landscapeSelected, selected_portrait: portraitSelected };
                    } else {
                        data = { success: false, error: 'Failed to select photos' };
                    }
                } else {
                    // On image-generation page, call image generation API
                    // Get current model and parameters from model selection panel
                    let model_name = 'gpt-image-1';
                    let parameters = {};
                    
                    if (window.modelSelectionPanel) {
                        model_name = window.modelSelectionPanel.currentModel || 'gpt-image-1';
                        parameters = window.modelSelectionPanel.parameters || {};
                    }
                    
                    const payload = {
                        image_prompt,
                        model_name,
                        parameters
                    };
                    resp = await fetch(`/imaging/api/image-generation/posts/${this.postId}/sections/${sectionId}/generate-image`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    data = await resp.json();
                }

                if (data.success) {
                    // Update output panel immediately if this section is highlighted
                    if (window.currentSubstage !== 'photo-selection') {
                        const imagePath = data.image_path || data.optimized_path; // Handle both APIs
                        if (window.imagingOutputPanel && this.currentSectionId === sectionId && imagePath) {
                            if (window.currentSubstage === 'optimise') {
                                window.imagingOutputPanel.onImageOptimized?.(imagePath);
                            } else {
                                window.imagingOutputPanel.onImageGenerated?.(imagePath);
                            }
                        }
                    }
                    this.callbacks.onBatchProgress({ current: i + 1, total: selectedIds.length, sectionId, sectionTitle, status: 'success' });
                } else {
                    this.callbacks.onBatchProgress({ current: i + 1, total: selectedIds.length, sectionId, sectionTitle, status: 'error', error: data.error });
                }

                // Small pacing delay
                if (i < selectedIds.length - 1) await new Promise(r => setTimeout(r, 500));
            }

            this.callbacks.onBatchComplete({ totalSections: selectedIds.length, successCount: selectedIds.length });
        } catch (err) {
            console.error('[ImagingSectionsPanel] Batch generation error:', err);
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = original; }
        }
    }

    updateSectionStatus(sectionId, newStatus) {
        // Update the section data
        const section = this.sections.find(s => s.id == sectionId);
        if (section) {
            section.status = newStatus;
        }

        // Update the UI
        const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (sectionElement) {
            sectionElement.dataset.status = newStatus;
            const statusElement = sectionElement.querySelector('.section-status');
            if (statusElement) {
                statusElement.className = `section-status ${newStatus}`;
                statusElement.textContent = newStatus.replace(/^./, c => c.toUpperCase());
            }
        }

        console.log(`[Imaging Sections Panel] Updated section ${sectionId} status to: ${newStatus}`);
    }
}

// Expose globally for imaging workspace
window.ImagingSectionsPanel = ImagingSectionsPanel;


