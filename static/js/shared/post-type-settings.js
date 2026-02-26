/**
 * Post Type Settings Modal
 * Displays contextual settings for current stage/substage with exploration capability
 */

(function() {
    'use strict';

    // Navigation structure (fallback when canonical API not used)
    const NAVIGATION_STRUCTURE = {
        'calendar': {
            label: 'Calendar',
            icon: 'fa-calendar-alt',
            substages: ['view', 'week-view', 'ideas-week']
        },
        'concept': {
            label: 'Planning',
            icon: 'fa-lightbulb',
            substages: ['taxonomy', 'section-structure', 'topic-allocation', 'titling']
        },
        'research': {
            label: 'Research',
            icon: 'fa-search',
            substages: ['research', 'sources', 'visuals', 'prompts', 'verification']
        },
        'authoring': {
            label: 'Authoring',
            icon: 'fa-pen-nib',
            substages: ['drafting', 'image-concepts', 'image-prompts', 'image-captions']
        },
        'imaging': {
            label: 'Imaging',
            icon: 'fa-magic',
            substages: ['image-generation', 'optimise']
        },
        'header': {
            label: 'Header',
            icon: 'fa-heading',
            substages: ['title-summary', 'image-prompt', 'image-details', 'image-generate', 'seo-meta']
        }
    };

    // Substage labels
    const SUBSTAGE_LABELS = {
        'view': 'Calendar View',
        'week-view': 'Week View',
        'ideas-week': 'Week Themes',
        'taxonomy': 'Taxonomy',
        'section-structure': 'Section Structure Design',
        'topic-allocation': 'Section Ideas',
        'titling': 'Section Titling',
        'research': 'Research Overview',
        'sources': 'Sources',
        'visuals': 'Visuals',
        'prompts': 'Prompts',
        'verification': 'Verification',
        'drafting': 'Drafting',
        'image-concepts': 'Image Concepts',
        'image-prompts': 'Image Prompts',
        'image-captions': 'Image Captions',
        'image-generation': 'Image Generation',
        'optimise': 'Optimise',
        'title-summary': 'Title & Summary',
        'image-prompt': 'Image Prompt',
        'image-details': 'Image Details',
        'image-generate': 'Image Generate',
        'seo-meta': 'SEO Meta'
    };

    // W2 Phase 1: Canonical substage registry (replaces SUBSTAGE_CONFIG_MAP when post context exists)
    const CANONICAL_STAGE_LABELS = {
        'metadata': 'Metadata',
        'ideas': 'Ideas',
        'structure': 'Structure',
        'titling': 'Titling',
        'authoring': 'Authoring',
        'imaging': 'Imaging',
        'review': 'Review'
    };

    // Minimal fallback when no post context (no canonical API). Keys match canonical substage ids.
    const FALLBACK_SUBSTAGE_CONFIG = {
        'ideas': { fromRegistry: false, title: 'Ideas', route: '-', template: null, pipelineStep: null, panels: null, llmConfig: null },
        'generate_idea_set': { fromRegistry: false, title: 'Generate Idea Set', route: '-', template: null, pipelineStep: null, panels: null, llmConfig: null },
        'generate-idea-set': { fromRegistry: false, title: 'Generate Idea Set', route: '-', template: null, pipelineStep: null, panels: null, llmConfig: null }
    };

    // For pipeline prev/next when not using canonical (stepId -> { stage, substage })
    const LEGACY_STEP_TO_SUBSTAGE = {
        'taxonomy': { stage: 'concept', substage: 'taxonomy' },
        'section-structure-design': { stage: 'concept', substage: 'section-structure' },
        'section-ideas': { stage: 'concept', substage: 'topic-allocation' },
        'section-titling': { stage: 'concept', substage: 'titling' },
        'week-ideas': { stage: 'calendar', substage: 'ideas-week' },
        'drafting': { stage: 'authoring', substage: 'drafting' },
        'image-concepts': { stage: 'authoring', substage: 'image-concepts' },
        'image-prompts': { stage: 'authoring', substage: 'image-prompts' },
        'image-captions': { stage: 'authoring', substage: 'image-captions' },
        'image-generation': { stage: 'imaging', substage: 'image-generation' },
        'optimise': { stage: 'imaging', substage: 'optimise' },
        'header-title-summary': { stage: 'header', substage: 'title-summary' },
        'header-image-prompt': { stage: 'header', substage: 'image-prompt' },
        'header-image-details': { stage: 'header', substage: 'image-details' },
        'header-image-generate': { stage: 'header', substage: 'image-generate' },
        'header-seo-meta': { stage: 'header', substage: 'seo-meta' }
    };

    class PostTypeSettingsModal {
        constructor() {
            this.modal = null;
            this.currentPostType = null;
            this.currentPostId = null;
            this.currentStage = null;
            this.currentSubstage = null;
            this.pipelineSteps = null;
            this.llmConfigs = null;
            this.panelConfigs = null;
            this.navigationStructure = null;
            this.canonicalSubstages = null; // From GET /api/posts/<id>/canonical-substages
            
            this.init();
        }

        init() {
            // Wait for DOM
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                this.setup();
            }
        }

        setup() {
            // Try to setup immediately, or wait for DOM
            const trySetup = () => {
                this.modal = document.getElementById('post-type-settings-modal');
                const openBtn = document.getElementById('post-type-settings-btn');
                
                if (!this.modal || !openBtn) {
                    // Retry after a short delay
                    setTimeout(trySetup, 100);
                    return;
                }

                const closeBtn = document.getElementById('post-type-settings-close');
                const overlay = this.modal.querySelector('.post-type-settings-overlay');

                // Setup open button
                openBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Post Type Settings: Opening modal');
                    this.open();
                });

                // Setup close button
                if (closeBtn) {
                    closeBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.close();
                    });
                }

                // Setup overlay click
                if (overlay) {
                    overlay.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.close();
                    });
                }

                // Close on Escape key
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && this.isOpen()) {
                        this.close();
                    }
                });
                
                console.log('Post Type Settings Modal: Initialized');
            };

            // Start setup
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', trySetup);
            } else {
                trySetup();
            }
        }

        isOpen() {
            return this.modal && this.modal.style.display !== 'none';
        }

        open() {
            if (!this.modal) return;

            // Get current context (W2 Phase 1: post ID for canonical registry)
            this.currentPostId = (typeof window.postId !== 'undefined' && window.postId) ? Number(window.postId) : null;
            this.currentPostType = this.getPostType();
            this.currentStage = window.currentStage || null;
            this.currentSubstage = window.currentSubstage || null;

            // Update modal title
            const title = document.getElementById('settings-modal-title');
            const badge = document.getElementById('settings-modal-post-type');
            if (title) title.textContent = 'Post Type Settings';
            if (badge) {
                badge.textContent = this.currentPostType ? this.currentPostType.toUpperCase() : '';
            }

            // Show modal
            this.modal.style.display = 'flex';

            // Build navigation and load settings (async)
            this.buildNavigation().then(() => {
                this.loadSettings(this.currentStage, this.currentSubstage);
            });
        }

        close() {
            if (this.modal) {
                this.modal.style.display = 'none';
            }
        }

        getPostType() {
            // Try to get from window
            if (window.postType) return window.postType.toLowerCase();
            
            // Try to get from header
            const header = document.querySelector('.post-type-value');
            if (header) {
                return header.textContent.trim().toLowerCase();
            }
            
            return 'themed'; // Default
        }

        async buildNavigation() {
            const tree = document.getElementById('navigation-tree');
            if (!tree) return;

            tree.innerHTML = '<div style="padding: 1rem; color: #94a3b8;">Loading navigation...</div>';
            this.canonicalSubstages = null;

            // W2 Phase 1: Prefer canonical registry when post context exists
            if (this.currentPostId) {
                try {
                    const response = await fetch(`/api/posts/${this.currentPostId}/canonical-substages`);
                    if (response.ok) {
                        const data = await response.json();
                        this.canonicalSubstages = data;
                        this.navigationStructure = this._navFromCanonical(data.stages || []);
                        this._renderNavTree(tree, this.navigationStructure, true);
                        return;
                    }
                } catch (e) {
                    console.warn('PostTypeSettingsModal: Canonical substages fetch failed, falling back', e);
                }
            }

            try {
                const response = await fetch(`/api/post-types/${this.currentPostType}/substages`);
                const data = await response.json();
                if (!data.success || !data.substages) {
                    throw new Error('Failed to load substage configuration');
                }
                const stageMetadata = {
                    'calendar': { label: 'Calendar', icon: 'fa-calendar-alt' },
                    'planning': { label: 'Planning', icon: 'fa-lightbulb' },
                    'research': { label: 'Research', icon: 'fa-search' },
                    'authoring': { label: 'Authoring', icon: 'fa-pen-nib' },
                    'imaging': { label: 'Imaging', icon: 'fa-magic' },
                    'header': { label: 'Header', icon: 'fa-heading' }
                };
                this.navigationStructure = data.substages;
                this._renderNavTree(tree, data.substages, false, stageMetadata);
            } catch (error) {
                console.error('Error building navigation:', error);
                tree.innerHTML = `<div style="padding: 1rem; color: #ef4444;">Error loading navigation: ${error.message}</div>`;
                this.buildNavigationFallback();
            }
        }

        _navFromCanonical(stages) {
            const out = {};
            (stages || []).forEach(s => {
                const stageKey = s.stage;
                out[stageKey] = (s.substages || []).map(sub => ({
                    key: sub.id,
                    label: sub.title || sub.id
                }));
            });
            return out;
        }

        _renderNavTree(tree, navStruct, fromCanonical, stageMetadata) {
            const meta = fromCanonical ? Object.fromEntries(
                Object.entries(CANONICAL_STAGE_LABELS).map(([k, v]) => [k, { label: v, icon: 'fa-circle' }])
            ) : (stageMetadata || {});
            const substageKeyToDataAttr = (key) => (key || '').replace(/_/g, '-');
            tree.innerHTML = '';
            Object.keys(navStruct).forEach(stageKey => {
                const substages = navStruct[stageKey];
                if (!substages || substages.length === 0) return;
                const stageMeta = meta[stageKey] || { label: stageKey, icon: 'fa-circle' };
                const isExpanded = stageKey === this.currentStage;
                const isActive = stageKey === this.currentStage;
                const stageDiv = document.createElement('div');
                stageDiv.className = `nav-stage ${isExpanded ? 'expanded' : ''}`;
                const header = document.createElement('div');
                header.className = `nav-stage-header ${isActive ? 'active' : ''}`;
                header.innerHTML = `<i class="fas ${stageMeta.icon} nav-stage-icon"></i><span>${stageMeta.label}</span>`;
                header.addEventListener('click', () => {
                    const isCurrentlyExpanded = stageDiv.classList.contains('expanded');
                    document.querySelectorAll('.nav-stage').forEach(s => s.classList.remove('expanded'));
                    if (!isCurrentlyExpanded) stageDiv.classList.add('expanded');
                });
                const substagesDiv = document.createElement('div');
                substagesDiv.className = 'nav-substages';
                substages.forEach(substage => {
                    const subKey = typeof substage === 'object' ? substage.key : substage;
                    const substageKey = substageKeyToDataAttr(subKey);
                    const substageLabel = (typeof substage === 'object' ? substage.label : null) || (subKey || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    const isSubstageActive = stageKey === this.currentStage && substageKey === this.currentSubstage;
                    const substageDiv = document.createElement('div');
                    substageDiv.className = `nav-substage ${isSubstageActive ? 'active' : ''}`;
                    substageDiv.textContent = substageLabel;
                    substageDiv.addEventListener('click', () => {
                        this.loadSettings(stageKey, substageKey);
                        document.querySelectorAll('.nav-substage').forEach(s => s.classList.remove('active'));
                        document.querySelectorAll('.nav-stage-header').forEach(s => s.classList.remove('active'));
                        substageDiv.classList.add('active');
                        header.classList.add('active');
                    });
                    substagesDiv.appendChild(substageDiv);
                });
                stageDiv.appendChild(header);
                stageDiv.appendChild(substagesDiv);
                tree.appendChild(stageDiv);
            });
        }

        _findConfigFromCanonical(stage, substage) {
            if (!this.canonicalSubstages || !this.canonicalSubstages.stages) return null;
            const stages = this.canonicalSubstages.stages;
            const substageNorm = (substage || '').replace(/-/g, '_');
            // Map planning+ideas to canonical ideas stage
            if ((stage === 'planning' || stage === 'ideas') && (substage === 'ideas' || substage === 'generate-idea-set' || substageNorm === 'generate_idea_set')) {
                const ideasStage = stages.find(s => s.stage === 'ideas');
                if (ideasStage && ideasStage.substages && ideasStage.substages.length) {
                    const sub = ideasStage.substages.find(s => s.id === 'generate_idea_set') || ideasStage.substages[0];
                    return { fromRegistry: true, title: sub.title, id: sub.id, route: '-', template: null, pipelineStep: null, panels: null, llmConfig: null };
                }
            }
            for (const s of stages) {
                const canonicalStage = s.stage;
                if (s.substages) {
                    for (const sub of s.substages) {
                        if ((s.stage === stage || (stage === 'planning' && canonicalStage === 'ideas')) && (sub.id === substageNorm || sub.id === substage)) {
                            return { fromRegistry: true, title: sub.title, id: sub.id, route: '-', template: null, pipelineStep: null, panels: null, llmConfig: null };
                        }
                    }
                }
            }
            return null;
        }

        _getSubstageLabel(stage, substage) {
            const fromCanon = this._findConfigFromCanonical(stage, substage);
            if (fromCanon) return fromCanon.title;
            const fallback = FALLBACK_SUBSTAGE_CONFIG[substage] || FALLBACK_SUBSTAGE_CONFIG[substage.replace(/-/g, '_')];
            if (fallback) return fallback.title;
            return (substage || '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        }

        buildNavigationFallback() {
            // Fallback to hardcoded structure if API fails
            const tree = document.getElementById('navigation-tree');
            if (!tree) return;

            tree.innerHTML = '';

            let filteredStages = { ...NAVIGATION_STRUCTURE };
            if (this.currentPostType === 'profile') {
                delete filteredStages['calendar'];
                delete filteredStages['research'];
            } else if (this.currentPostType === 'recipe') {
                delete filteredStages['research'];
            }

            Object.keys(filteredStages).forEach(stageKey => {
                const stage = filteredStages[stageKey];
                const isExpanded = stageKey === this.currentStage;
                const isActive = stageKey === this.currentStage;

                const stageDiv = document.createElement('div');
                stageDiv.className = `nav-stage ${isExpanded ? 'expanded' : ''}`;

                const header = document.createElement('div');
                header.className = `nav-stage-header ${isActive ? 'active' : ''}`;
                header.innerHTML = `
                    <i class="fas ${stage.icon} nav-stage-icon"></i>
                    <span>${stage.label}</span>
                `;
                header.addEventListener('click', () => {
                    const isCurrentlyExpanded = stageDiv.classList.contains('expanded');
                    document.querySelectorAll('.nav-stage').forEach(s => s.classList.remove('expanded'));
                    if (!isCurrentlyExpanded) {
                        stageDiv.classList.add('expanded');
                    }
                });

                const substagesDiv = document.createElement('div');
                substagesDiv.className = 'nav-substages';

                stage.substages.forEach(substageKey => {
                    const substageLabel = SUBSTAGE_LABELS[substageKey] || substageKey;
                    const isSubstageActive = stageKey === this.currentStage && substageKey === this.currentSubstage;

                    const substageDiv = document.createElement('div');
                    substageDiv.className = `nav-substage ${isSubstageActive ? 'active' : ''}`;
                    substageDiv.textContent = substageLabel;
                    substageDiv.addEventListener('click', () => {
                        this.loadSettings(stageKey, substageKey);
                        document.querySelectorAll('.nav-substage').forEach(s => s.classList.remove('active'));
                        document.querySelectorAll('.nav-stage-header').forEach(s => s.classList.remove('active'));
                        substageDiv.classList.add('active');
                        header.classList.add('active');
                    });

                    substagesDiv.appendChild(substageDiv);
                });

                stageDiv.appendChild(header);
                stageDiv.appendChild(substagesDiv);
                tree.appendChild(stageDiv);
            });
        }

        async loadSettings(stage, substage) {
            const loading = document.getElementById('settings-loading');
            const content = document.getElementById('settings-content');
            const error = document.getElementById('settings-error');
            const contextValue = document.getElementById('context-value');

            // Show loading
            if (loading) loading.style.display = 'flex';
            if (content) content.style.display = 'none';
            if (error) error.style.display = 'none';

            // Update context
            if (contextValue) {
                const stageLabels = { ...CANONICAL_STAGE_LABELS, calendar: 'Calendar', planning: 'Planning', research: 'Research', authoring: 'Authoring', imaging: 'Imaging', header: 'Header' };
                const stageLabel = stageLabels[stage] || stage;
                const substageLabel = this._getSubstageLabel(stage, substage);
                contextValue.textContent = `${stageLabel} > ${substageLabel}`;
            }

            try {
                // W2 Phase 1: Resolve config from canonical registry first, then minimal fallback
                let config = this._findConfigFromCanonical(stage, substage);
                if (!config) {
                    config = FALLBACK_SUBSTAGE_CONFIG[substage] || FALLBACK_SUBSTAGE_CONFIG[substage.replace(/-/g, '_')];
                }
                if (!config) {
                    throw new Error(`No configuration found for substage: ${substage}`);
                }

                // Load pipeline steps if needed
                if (!this.pipelineSteps) {
                    await this.loadPipelineSteps();
                }

                // Load LLM configs if needed
                if (!this.llmConfigs) {
                    this.llmConfigs = window.LLM_CONFIGS || {};
                }

                // Load panel configs if needed
                if (!this.panelConfigs) {
                    await this.loadPanelConfigs();
                }

                // Display settings (async - will fetch template from API)
                await this.displaySettings(stage, substage, config);

                // Hide loading, show content
                if (loading) loading.style.display = 'none';
                if (content) content.style.display = 'block';

            } catch (err) {
                console.error('Error loading settings:', err);
                if (loading) loading.style.display = 'none';
                if (error) {
                    error.style.display = 'flex';
                    const errorMsg = document.getElementById('settings-error-message');
                    if (errorMsg) errorMsg.textContent = err.message || 'Failed to load settings';
                }
            }
        }

        async loadPipelineSteps() {
            try {
                const response = await fetch(`/api/settings/post-types/${this.currentPostType}/pipeline-steps`);
                if (response.ok) {
                    const data = await response.json();
                    this.pipelineSteps = data.steps || [];
                }
            } catch (err) {
                console.warn('Failed to load pipeline steps:', err);
                this.pipelineSteps = [];
            }
        }

        async loadPanelConfigs() {
            try {
                const response = await fetch(`/api/settings/post-types/${this.currentPostType}/panels`);
                if (response.ok) {
                    const data = await response.json();
                    this.panelConfigs = data;
                }
            } catch (err) {
                console.warn('Failed to load panel configs:', err);
                this.panelConfigs = null;
            }
        }

        async displaySettings(stage, substage, config) {
            // Fetch actual template path from backend API
            try {
                const response = await fetch(`/api/settings/post-types/${this.currentPostType}/context/${stage}/${substage}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.template) {
                        document.getElementById('template-path').textContent = data.template.path || '-';
                        document.getElementById('template-post-type-specific').textContent = 
                            data.template.is_post_type_specific ? 'Yes' : 'No';
                    } else {
                        // Fallback to config mapping
                        this.displayTemplateFromConfig(config);
                    }
                } else {
                    // Fallback to config mapping
                    this.displayTemplateFromConfig(config);
                }
            } catch (err) {
                console.warn('Failed to fetch template from API, using config:', err);
                // Fallback to config mapping
                this.displayTemplateFromConfig(config);
            }
            
            document.getElementById('template-route').textContent = config.route || '-';

            // Action Buttons
            const actionSection = document.getElementById('action-buttons-section');
            const actionList = document.getElementById('action-buttons-list');
            
            // Check for profile-specific config first
            let llmConfigKey = config.llmConfig;
            if (this.currentPostType === 'profile' && config.llmConfigProfile) {
                llmConfigKey = config.llmConfigProfile;
            }
            
            // For profile section structure, use custom endpoint
            if (substage === 'section-structure' && this.currentPostType === 'profile') {
                actionList.innerHTML = `
                    <div class="action-button-item">
                        <div class="action-button-label">Generate Section Structure</div>
                        <div class="action-button-endpoint">
                            <span class="action-button-method">POST</span>
                            /planning/api/profile/section-structure
                        </div>
                        <div class="settings-item">
                            <div class="settings-label">Prompt:</div>
                            <div class="settings-value">Product Profile Section Structure</div>
                        </div>
                    </div>
                `;
                if (actionSection) actionSection.style.display = 'block';
            } else if (llmConfigKey && this.llmConfigs[llmConfigKey]) {
                const llmConfig = this.llmConfigs[llmConfigKey];
                actionList.innerHTML = `
                    <div class="action-button-item">
                        <div class="action-button-label">Generate</div>
                        <div class="action-button-endpoint">
                            <span class="action-button-method">POST</span>
                            ${llmConfig.generateEndpoint || '-'}
                        </div>
                        ${llmConfig.promptEndpoint ? `
                            <div class="settings-item">
                                <div class="settings-label">Prompt Endpoint:</div>
                                <div class="settings-value code">${llmConfig.promptEndpoint}</div>
                            </div>
                        ` : ''}
                        <div class="settings-item">
                            <div class="settings-label">Results Field:</div>
                            <div class="settings-value code">${llmConfig.resultsField || '-'}</div>
                        </div>
                    </div>
                `;
                if (actionSection) actionSection.style.display = 'block';
            } else {
                if (actionSection) actionSection.style.display = 'none';
            }

            // Pipeline Step (hidden when from canonical registry; prev/next use LEGACY_STEP_TO_SUBSTAGE)
            const pipelineSection = document.getElementById('pipeline-step-section');
            if (config.pipelineStep && !config.fromRegistry && this.pipelineSteps) {
                const step = this.pipelineSteps.find(s => s.stepId === config.pipelineStep);
                if (step) {
                    document.getElementById('pipeline-step-id').textContent = step.stepId || '-';
                    document.getElementById('pipeline-step-order').textContent = step.order || '-';
                    document.getElementById('pipeline-step-label').textContent = step.label || '-';
                    document.getElementById('pipeline-step-function').textContent = step.function || '-';

                    const nav = document.getElementById('pipeline-navigation');
                    if (step.previous || step.next) {
                        if (step.previous) {
                            document.getElementById('pipeline-prev-label').textContent = step.previous.label;
                            document.getElementById('pipeline-prev').classList.remove('disabled');
                            document.getElementById('pipeline-prev').onclick = () => {
                                const prevInfo = LEGACY_STEP_TO_SUBSTAGE[step.previous.stepId];
                                if (prevInfo) this.loadSettings(prevInfo.stage, prevInfo.substage);
                            };
                        } else {
                            document.getElementById('pipeline-prev').classList.add('disabled');
                        }
                        if (step.next) {
                            document.getElementById('pipeline-next-label').textContent = step.next.label;
                            document.getElementById('pipeline-next').classList.remove('disabled');
                            document.getElementById('pipeline-next').onclick = () => {
                                const nextInfo = LEGACY_STEP_TO_SUBSTAGE[step.next.stepId];
                                if (nextInfo) this.loadSettings(nextInfo.stage, nextInfo.substage);
                            };
                        } else {
                            document.getElementById('pipeline-next').classList.add('disabled');
                        }
                        if (nav) nav.style.display = 'flex';
                    } else {
                        if (nav) nav.style.display = 'none';
                    }
                    if (pipelineSection) pipelineSection.style.display = 'block';
                } else {
                    if (pipelineSection) pipelineSection.style.display = 'none';
                }
            } else {
                if (pipelineSection) pipelineSection.style.display = 'none';
            }

            // Panel Configuration
            const panelSection = document.getElementById('panel-config-section');
            if (config.panels && this.panelConfigs) {
                const panels = this.panelConfigs.panels || [];
                document.getElementById('panel-list').innerHTML = panels.map((p, i) => `
                    <div class="panel-list-item">
                        <span class="panel-order">${i + 1}</span>
                        <span>${p.type}</span>
                    </div>
                `).join('') || '-';
                document.getElementById('panel-output').textContent = this.panelConfigs.output_panel || '-';
                if (panelSection) panelSection.style.display = 'block';
            } else {
                if (panelSection) panelSection.style.display = 'none';
            }

            // Navbar (use current nav structure when from canonical)
            let navbarVisible = false;
            if (this.navigationStructure) {
                const subToKey = (sub) => ((typeof sub === 'object' ? sub.key : sub) || '').replace(/_/g, '-');
                navbarVisible = Object.keys(this.navigationStructure).some(s =>
                    (this.navigationStructure[s] || []).some(sub => subToKey(sub) === substage)
                );
            }
            if (!navbarVisible) {
                navbarVisible = Object.values(NAVIGATION_STRUCTURE).some(s => s.substages.includes(substage));
            }
            document.getElementById('navbar-visible').textContent = navbarVisible ? 'Yes' : 'No';
            document.getElementById('navbar-post-types').textContent = 
                this.getNavbarPostTypes(stage, substage).join(', ') || 'All';
        }

        displayTemplateFromConfig(config) {
            if (!config || config.template == null) {
                document.getElementById('template-path').textContent = '-';
                document.getElementById('template-post-type-specific').textContent = 'No';
                return;
            }
            const template = typeof config.template === 'object'
                ? (config.template[this.currentPostType] || config.template['default'])
                : config.template;
            document.getElementById('template-path').textContent = template || '-';
            document.getElementById('template-post-type-specific').textContent =
                typeof config.template === 'object' ? 'Yes' : 'No';
        }

        getNavbarPostTypes(stage, substage) {
            // This is a simplified version - in reality, we'd check the template
            // For now, return all post types that have this substage
            return ['themed', 'profile', 'recipe', 'generated'];
        }
    }

    // Initialize on load
    let settingsModal = null;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            settingsModal = new PostTypeSettingsModal();
        });
    } else {
        settingsModal = new PostTypeSettingsModal();
    }

    // Make available globally
    window.PostTypeSettingsModal = PostTypeSettingsModal;

})();

