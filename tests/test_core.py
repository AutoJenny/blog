import unittest
from app import create_app
from app.core.models.core_model import CoreModel
from app.core.schemas.core_schema import CoreSchema
from app.core.utils.core_utils import get_core_data

class TestCoreModule(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_health_check_endpoint(self):
        """Test the health check endpoint returns 200 OK"""
        response = self.client.get('/core/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_core_model(self):
        """Test the core model creation and attributes"""
        model = CoreModel(id=1, name="Test Model")
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "Test Model")

    def test_core_schema(self):
        """Test the core schema serialization"""
        schema = CoreSchema()
        data = {'id': 1, 'name': 'Test Schema'}
        result = schema.load(data)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], 'Test Schema')

    def test_core_utils(self):
        """Test the core utility function"""
        result = get_core_data()
        self.assertEqual(result, {'message': 'Core utility function'})

if __name__ == '__main__':
    unittest.main() 