/**
 * Post Section Selection Management
 * Handles section selection and generation
 */

class PostSectionSelection {
    constructor(dataManager) {
        this.dataManager = dataManager;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const generateBtn = document.getElementById('generateAllSectionsBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this.generateAllSections();
            });
        }
    }

    async generateAllSections() {
        const post = this.dataManager.getCurrentPost();
        const sections = this.dataManager.getCurrentSections();

        if (!post || sections.length === 0) {
            alert('Please select a post with sections first.');
            return;
        }

        const generateBtn = document.getElementById('generateAllSectionsBtn');
        const originalText = generateBtn.innerHTML;

        try {
            // Disable button and show progress
            PostSectionUtils.setButtonState('generateAllSectionsBtn', true, 
                '<i class="fas fa-spinner fa-spin me-2"></i>Generating...');
            PostSectionUtils.showProgress(true);

            let completedCount = 0;
            const totalCount = sections.length;

            // Generate content for each section
            for (const section of sections) {
                try {
                    await this.generateSectionContent(section);
                    completedCount++;
                    
                    // Update progress
                    const progress = Math.round((completedCount / totalCount) * 100);
                    PostSectionUtils.updateProgress(progress, 
                        `Generated ${completedCount} of ${totalCount} sections`);
                    
                } catch (error) {
                    console.error(`Error generating content for section ${section.id}:`, error);
                }
            }

            // Complete
            PostSectionUtils.updateProgress(100, 'All sections generated successfully!');
            setTimeout(() => {
                PostSectionUtils.showProgress(false);
                PostSectionUtils.setButtonState('generateAllSectionsBtn', false, originalText);
            }, 1000);

        } catch (error) {
            console.error('Error generating all sections:', error);
            PostSectionUtils.showProgress(false);
            PostSectionUtils.setButtonState('generateAllSectionsBtn', false, originalText);
            alert('Error generating content. Please try again.');
        }
    }

    async generateSectionContent(section) {
        // This will be implemented to work with the AI content generation system
        // For now, just simulate the process
        return new Promise(resolve => {
            setTimeout(() => {
                console.log(`Generated content for section: ${section.section_heading}`);
                resolve();
            }, 1000);
        });
    }

    selectSection(section) {
        this.dataManager.setSelectedSection(section);
        
        // Dispatch event for other modules
        PostSectionUtils.dispatchEvent('sectionSelected', {
            section: section,
            post: this.dataManager.getCurrentPost()
        });
    }

    getSelectedSection() {
        return this.dataManager.getSelectedSection();
    }
}
