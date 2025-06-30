"""Test data for workflow navigation module."""

# Test workflow stages
TEST_STAGES = [
    {
        'id': 1,
        'name': 'planning',
        'description': 'Planning stage',
        'stage_order': 1
    },
    {
        'id': 2,
        'name': 'writing',
        'description': 'Writing stage',
        'stage_order': 2
    },
    {
        'id': 3,
        'name': 'publishing',
        'description': 'Publishing stage',
        'stage_order': 3
    }
]

# Test workflow substages
TEST_SUBSTAGES = [
    {
        'id': 1,
        'stage_id': 1,
        'name': 'idea',
        'description': 'Idea substage',
        'sub_stage_order': 1
    },
    {
        'id': 2,
        'stage_id': 1,
        'name': 'research',
        'description': 'Research substage',
        'sub_stage_order': 2
    },
    {
        'id': 3,
        'stage_id': 1,
        'name': 'structure',
        'description': 'Structure substage',
        'sub_stage_order': 3
    },
    {
        'id': 4,
        'stage_id': 2,
        'name': 'content',
        'description': 'Content substage',
        'sub_stage_order': 1
    },
    {
        'id': 5,
        'stage_id': 2,
        'name': 'meta_info',
        'description': 'Meta info substage',
        'sub_stage_order': 2
    },
    {
        'id': 6,
        'stage_id': 2,
        'name': 'images',
        'description': 'Images substage',
        'sub_stage_order': 3
    },
    {
        'id': 7,
        'stage_id': 3,
        'name': 'preflight',
        'description': 'Preflight substage',
        'sub_stage_order': 1
    },
    {
        'id': 8,
        'stage_id': 3,
        'name': 'launch',
        'description': 'Launch substage',
        'sub_stage_order': 2
    },
    {
        'id': 9,
        'stage_id': 3,
        'name': 'syndication',
        'description': 'Syndication substage',
        'sub_stage_order': 3
    }
]

# Test workflow steps
TEST_STEPS = [
    {
        'id': 1,
        'sub_stage_id': 1,
        'name': 'basic_idea',
        'description': 'Basic idea step',
        'step_order': 1
    },
    {
        'id': 2,
        'sub_stage_id': 1,
        'name': 'provisional_title',
        'description': 'Provisional title step',
        'step_order': 2
    },
    {
        'id': 3,
        'sub_stage_id': 2,
        'name': 'concepts',
        'description': 'Concepts step',
        'step_order': 1
    },
    {
        'id': 4,
        'sub_stage_id': 2,
        'name': 'facts',
        'description': 'Facts step',
        'step_order': 2
    },
    {
        'id': 5,
        'sub_stage_id': 3,
        'name': 'outline',
        'description': 'Outline step',
        'step_order': 1
    },
    {
        'id': 6,
        'sub_stage_id': 3,
        'name': 'allocate_facts',
        'description': 'Allocate facts step',
        'step_order': 2
    }
]

# Test posts
TEST_POSTS = [
    {
        'id': 1,
        'title': 'Test Post 1',
        'slug': 'test-post-1',
        'status': 'draft'
    },
    {
        'id': 2,
        'title': 'Test Post 2',
        'slug': 'test-post-2',
        'status': 'draft'
    }
] 