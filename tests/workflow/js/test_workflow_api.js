describe('Workflow API Configuration', () => {
    it('should have correct base URL', () => {
        expect(API_CONFIG.BASE_URL).toBe('/api/workflow');
    });

    it('should have all required endpoints', () => {
        expect(API_CONFIG.ENDPOINTS).toHaveProperty('POSTS');
        expect(API_CONFIG.ENDPOINTS).toHaveProperty('FIELDS');
        expect(API_CONFIG.ENDPOINTS).toHaveProperty('PROMPTS');
        expect(API_CONFIG.ENDPOINTS).toHaveProperty('LLM');
    });

    it('should build valid post URLs', () => {
        const postId = 123;
        const url = buildWorkflowUrl('POSTS', postId);
        expect(url).toBe('/api/workflow/posts/123');
    });

    it('should build valid field mapping URLs', () => {
        const url = buildWorkflowUrl('FIELDS', 'mappings');
        expect(url).toBe('/api/workflow/fields/mappings');
    });
});

describe('Workflow API Calls', () => {
    beforeEach(() => {
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    it('should fetch post details', async () => {
        const postId = 123;
        const mockResponse = { id: postId, title: 'Test Post' };
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const response = await fetchPostDetails(postId);
        expect(response).toEqual(mockResponse);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/workflow/posts/123',
            expect.any(Object)
        );
    });

    it('should handle field mapping updates', async () => {
        const mappingData = { field: 'test', value: 'test value' };
        const mockResponse = { success: true };
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const response = await updateFieldMapping(mappingData);
        expect(response).toEqual(mockResponse);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/workflow/fields/mappings',
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(mappingData)
            })
        );
    });

    it('should handle errors appropriately', async () => {
        const postId = 123;
        global.fetch.mockRejectedValueOnce(new Error('Network error'));

        await expect(fetchPostDetails(postId)).rejects.toThrow('Network error');
    });
}); 