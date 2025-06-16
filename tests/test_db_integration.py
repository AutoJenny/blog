import unittest
import os
from app.utils.db import (
    init_db_pool,
    verify_workflow_tables,
    get_workflow_stages,
    get_post_workflow_status,
    update_post_workflow_status,
    get_workflow_step_actions
)

class TestDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Ensure we're using test database
        os.environ['POSTGRES_DB'] = 'blog_test'
        init_db_pool()

    def test_workflow_tables_exist(self):
        """Test that all required workflow tables exist."""
        self.assertTrue(verify_workflow_tables())

    def test_get_workflow_stages(self):
        """Test retrieving workflow stages."""
        stages = get_workflow_stages()
        self.assertIsInstance(stages, list)
        if stages:
            self.assertIn('stage_name', stages[0])
            self.assertIn('sub_stage_name', stages[0])
            self.assertIn('step_name', stages[0])

    def test_post_workflow_status(self):
        """Test post workflow status operations."""
        # Test getting status for a non-existent post
        status = get_post_workflow_status(999999)
        self.assertEqual(len(status), 0)

        # Test updating status for a non-existent post
        update_post_workflow_status(999999, 1, 'in_progress')
        status = get_post_workflow_status(999999)
        self.assertEqual(len(status), 0)

    def test_workflow_step_actions(self):
        """Test retrieving workflow step actions."""
        # Test getting actions for a non-existent step
        actions = get_workflow_step_actions(999999)
        self.assertEqual(len(actions), 0)

if __name__ == '__main__':
    unittest.main() 