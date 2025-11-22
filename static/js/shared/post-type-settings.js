/**
 * Post Type Settings Modal
 * Displays contextual settings for current stage/substage with exploration capability
 */

(function() {
    'use strict';

    // Substage to configuration mapping
    const SUBSTAGE_CONFIG_MAP = {
        // Calendar substages
        'view': {
            template: 'planning/calendar/view.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_calendar_view'
        },
        'week-view': {
            template: 'planning/calendar/week_view.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_calendar_week_view'
        },
        'ideas-week': {
            template: 'planning/calendar/ideas_week.html',
            llmConfig: null,
            pipelineStep: 'week-ideas',
            panels: null,
            route: null
        },
        
        // Planning substages
        'taxonomy': {
            template: 'planning/calendar/taxonomy.html',
            llmConfig: null,
            pipelineStep: 'taxonomy',
            panels: null,
            route: 'planning.planning_calendar_taxonomy'
        },
        'section-structure': {
            template: {
                'profile': 'planning/concept/section_structure_profile.html',
                'default': 'planning/concept/section_structure.html'
            },
            llmConfig: null, // Profile uses different endpoint
            llmConfigProfile: 'section_structure_profile', // Custom for profile
            pipelineStep: 'section-structure-design',
            panels: null,
            route: 'planning.planning_concept_section_structure'
        },
        'topic-allocation': {
            template: {
                'profile': 'planning/concept/topic_allocation_profile.html',
                'default': 'planning/concept/topic_allocation.html'
            },
            llmConfig: 'topic_allocation',
            pipelineStep: 'section-ideas',
            panels: null,
            route: 'planning.planning_concept_topic_allocation'
        },
        'titling': {
            template: {
                'profile': 'planning/concept/titling_profile.html',
                'default': 'planning/concept/titling.html'
            },
            llmConfig: 'titling',
            pipelineStep: 'section-titling',
            panels: null,
            route: 'planning.planning_concept_titling'
        },
        
        // Research substages
        'research': {
            template: 'planning/research/index.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_research'
        },
        'sources': {
            template: 'planning/research/sources.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_research_sources'
        },
        'visuals': {
            template: 'planning/research/visuals.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_research_visuals'
        },
        'prompts': {
            template: 'planning/research/prompts.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_research_prompts'
        },
        'verification': {
            template: 'planning/research/verification.html',
            llmConfig: null,
            pipelineStep: null,
            panels: null,
            route: 'planning.planning_research_verification'
        },
        
        // Authoring substages
        'drafting': {
            template: 'authoring/sections/drafting.html',
            llmConfig: 'author_draft',
            pipelineStep: 'drafting',
            panels: 'authoring',
            route: 'authoring.authoring_sections_drafting'
        },
        'image-concepts': {
            template: 'authoring/sections/image_concepts.html',
            llmConfig: 'image_concepts',
            pipelineStep: 'image-concepts',
            panels: 'authoring',
            route: 'authoring_imaging.authoring_sections_image_concepts'
        },
        'image-prompts': {
            template: 'authoring/sections/image_prompts.html',
            llmConfig: 'image_prompts',
            pipelineStep: 'image-prompts',
            panels: 'authoring',
            route: 'authoring_imaging.authoring_sections_image_prompts'
        },
        'image-captions': {
            template: 'authoring/sections/image_captions.html',
            llmConfig: 'image_captions',
            pipelineStep: 'image-captions',
            panels: 'authoring',
            route: 'authoring_imaging.authoring_sections_image_captions'
        },
        
        // Imaging substages
        'image-generation': {
            template: {
                'profile': 'imaging/sections/image_generation_profile.html',
                'default': 'imaging/sections/image_generation.html'
            },
            llmConfig: 'image_generation',
            pipelineStep: 'image-generation',
            panels: null,
            route: 'imaging.imaging_sections_image_generation'
        },
        'optimise': {
            template: 'imaging/sections/optimise.html',
            llmConfig: null,
            pipelineStep: 'optimise',
            panels: null,
            route: 'imaging.imaging_sections_optimise'
        },
        
        // Header substages
        'title-summary': {
            template: 'header/title_summary.html',
            llmConfig: null,
            pipelineStep: 'header-title-summary',
            panels: null,
            route: 'header.header_title_summary'
        },
        'image-prompt': {
            template: 'header/image_prompt.html',
            llmConfig: null,
            pipelineStep: 'header-image-prompt',
            panels: null,
            route: 'header.header_image_prompt'
        },
        'image-details': {
            template: 'header/image_details.html',
            llmConfig: null,
            pipelineStep: 'header-image-details',
            panels: null,
            route: 'header.header_image_details'
        },
        'image-generate': {
            template: 'header/image_generate.html',
            llmConfig: null,
            pipelineStep: 'header-image-generate',
            panels: null,
            route: 'header.header_image_generate'
        },
        'seo-meta': {
            template: 'header/seo_meta.html',
            llmConfig: null,
            pipelineStep: 'header-seo-meta',
            panels: null,
            route: 'header.header_seo_meta'
        }
    };

    // Navigation structure
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

    class PostTypeSettingsModal {
        constructor() {
            this.modal = null;
            this.currentPostType = null;
            this.currentStage = null;
            this.currentSubstage = null;
            this.pipelineSteps = null;
            this.llmConfigs = null;
            this.panelConfigs = null;
            
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

            // Get current context
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

            // Build navigation and load settings
            this.buildNavigation();
            this.loadSettings(this.currentStage, this.currentSubstage);
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

        buildNavigation() {
            const tree = document.getElementById('navigation-tree');
            if (!tree) return;

            tree.innerHTML = '';

            // Filter navigation based on post type
            let filteredStages = { ...NAVIGATION_STRUCTURE };
            if (this.currentPostType === 'profile') {
                // Profile posts don't have Calendar or Research
                delete filteredStages['calendar'];
                delete filteredStages['research'];
            } else if (this.currentPostType === 'recipe') {
                // Recipe posts don't have Research
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
                        // Update active states
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
                const stageLabel = NAVIGATION_STRUCTURE[stage]?.label || stage;
                const substageLabel = SUBSTAGE_LABELS[substage] || substage;
                contextValue.textContent = `${stageLabel} > ${substageLabel}`;
            }

            try {
                // Get configuration
                const config = SUBSTAGE_CONFIG_MAP[substage];
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

            // Pipeline Step
            const pipelineSection = document.getElementById('pipeline-step-section');
            if (config.pipelineStep && this.pipelineSteps) {
                const step = this.pipelineSteps.find(s => s.stepId === config.pipelineStep);
                if (step) {
                    document.getElementById('pipeline-step-id').textContent = step.stepId || '-';
                    document.getElementById('pipeline-step-order').textContent = step.order || '-';
                    document.getElementById('pipeline-step-label').textContent = step.label || '-';
                    document.getElementById('pipeline-step-function').textContent = step.function || '-';

                    // Navigation
                    const nav = document.getElementById('pipeline-navigation');
                    if (step.previous || step.next) {
                        if (step.previous) {
                            document.getElementById('pipeline-prev-label').textContent = step.previous.label;
                            document.getElementById('pipeline-prev').classList.remove('disabled');
                            document.getElementById('pipeline-prev').onclick = () => {
                                const prevSubstage = Object.keys(SUBSTAGE_CONFIG_MAP).find(
                                    k => SUBSTAGE_CONFIG_MAP[k].pipelineStep === step.previous.stepId
                                );
                                if (prevSubstage) {
                                    const prevStage = Object.keys(NAVIGATION_STRUCTURE).find(
                                        s => NAVIGATION_STRUCTURE[s].substages.includes(prevSubstage)
                                    );
                                    if (prevStage) this.loadSettings(prevStage, prevSubstage);
                                }
                            };
                        } else {
                            document.getElementById('pipeline-prev').classList.add('disabled');
                        }
                        if (step.next) {
                            document.getElementById('pipeline-next-label').textContent = step.next.label;
                            document.getElementById('pipeline-next').classList.remove('disabled');
                            document.getElementById('pipeline-next').onclick = () => {
                                const nextSubstage = Object.keys(SUBSTAGE_CONFIG_MAP).find(
                                    k => SUBSTAGE_CONFIG_MAP[k].pipelineStep === step.next.stepId
                                );
                                if (nextSubstage) {
                                    const nextStage = Object.keys(NAVIGATION_STRUCTURE).find(
                                        s => NAVIGATION_STRUCTURE[s].substages.includes(nextSubstage)
                                    );
                                    if (nextStage) this.loadSettings(nextStage, nextSubstage);
                                }
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

            // Navbar
            const navbarVisible = Object.values(NAVIGATION_STRUCTURE).some(
                s => s.substages.includes(substage)
            );
            document.getElementById('navbar-visible').textContent = navbarVisible ? 'Yes' : 'No';
            document.getElementById('navbar-post-types').textContent = 
                this.getNavbarPostTypes(stage, substage).join(', ') || 'All';
        }

        displayTemplateFromConfig(config) {
            // Fallback: Use config mapping if API fails
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

