describe('Workflow Navigation', () => {
    beforeEach(() => {
        // Mock window.location
        delete window.location;
        window.location = { href: '' };
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    it('should navigate to correct workflow stage', () => {
        const postId = 123;
        const stage = 'planning';
        const substage = 'idea';
        
        navigateToWorkflow(postId, stage, substage);
        expect(window.location.href).toBe('/workflow/posts/123/planning/idea');
    });

    it('should handle navigation without substage', () => {
        const postId = 123;
        const stage = 'planning';
        
        navigateToWorkflow(postId, stage);
        expect(window.location.href).toBe('/workflow/posts/123/planning');
    });

    it('should validate parameters before navigation', () => {
        expect(() => navigateToWorkflow()).toThrow('Post ID is required');
        expect(() => navigateToWorkflow(123)).toThrow('Stage is required');
    });

    it('should handle back navigation', () => {
        const postId = 123;
        
        navigateToWorkflowHome(postId);
        expect(window.location.href).toBe('/workflow/posts/123');
    });
});

describe('Workflow Stage Management', () => {
    it('should track current stage', () => {
        const postId = 123;
        const stage = 'planning';
        const substage = 'idea';
        
        setCurrentStage(postId, stage, substage);
        const current = getCurrentStage(postId);
        
        expect(current).toEqual({
            stage: 'planning',
            substage: 'idea'
        });
    });

    it('should validate stage transitions', () => {
        const postId = 123;
        
        setCurrentStage(postId, 'planning', 'idea');
        expect(canTransitionTo(postId, 'planning', 'scope')).toBe(true);
        expect(canTransitionTo(postId, 'publishing')).toBe(false);
    });

    it('should handle stage completion', () => {
        const postId = 123;
        const stage = 'planning';
        const substage = 'idea';
        
        markStageComplete(postId, stage, substage);
        expect(isStageComplete(postId, stage, substage)).toBe(true);
    });
}); 