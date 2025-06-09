// Clean implementation of workflow functionality
class WorkflowManager {
    constructor() {
        this.currentStage = null;
        this.currentSubstage = null;
        this.postId = null;
    }

    init(stage, substage, postId) {
        this.currentStage = stage;
        this.currentSubstage = substage;
        this.postId = postId;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Will be implemented for each substage
    }

    // Common utility methods
    async fetchData(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Error fetching data:', error);
            throw error;
        }
    }

    async saveData(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Error saving data:', error);
            throw error;
        }
    }
}

// Export for use in other files
window.WorkflowManager = WorkflowManager; 