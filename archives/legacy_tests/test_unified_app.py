#!/usr/bin/env python3
"""
Comprehensive Testing Script for Unified BlogForge Application
Tests all blueprints, endpoints, and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple

class UnifiedAppTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                     data: Dict = None, headers: Dict = None) -> bool:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                self.results['passed'] += 1
                print(f"✅ {method} {endpoint} - {response.status_code}")
                return True
            else:
                self.results['failed'] += 1
                error_msg = f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}"
                print(error_msg)
                self.results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            self.results['failed'] += 1
            error_msg = f"❌ {method} {endpoint} - Exception: {str(e)}"
            print(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def test_core_blueprint(self):
        """Test core blueprint endpoints"""
        print("\n🔍 Testing Core Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/')
        self.test_endpoint('GET', '/health')
        self.test_endpoint('GET', '/api/posts')
        self.test_endpoint('GET', '/workflow/')
        self.test_endpoint('GET', '/workflow/posts/1')
        self.test_endpoint('GET', '/workflow/posts/1/planning')
        self.test_endpoint('GET', '/workflow/posts/1/planning/idea')
        self.test_endpoint('GET', '/workflow/posts/1/planning/idea/initial_concept')
        
        # Test database endpoints
        self.test_endpoint('GET', '/db/test')
        self.test_endpoint('GET', '/db/simple')
    
    def test_launchpad_blueprint(self):
        """Test launchpad blueprint endpoints"""
        print("\n🚀 Testing Launchpad Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/launchpad/')
        self.test_endpoint('GET', '/launchpad/cross-promotion')
        self.test_endpoint('GET', '/launchpad/publishing')
        self.test_endpoint('GET', '/launchpad/social-media-command-center')
        self.test_endpoint('GET', '/launchpad/syndication')
        
        # Test API endpoints
        self.test_endpoint('GET', '/launchpad/api/social-media/timeline')
        self.test_endpoint('GET', '/launchpad/api/syndication/social-media-platforms')
        self.test_endpoint('GET', '/launchpad/api/syndication/content-processes')
        
        # Test syndication channel configs
        self.test_endpoint('GET', '/launchpad/syndication/facebook/blog_post')
        self.test_endpoint('GET', '/launchpad/syndication/facebook/product_post')
    
    def test_llm_actions_blueprint(self):
        """Test LLM actions blueprint endpoints"""
        print("\n🤖 Testing LLM Actions Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/llm-actions/')
        self.test_endpoint('GET', '/llm-actions/health')
        
        # Test API endpoints
        self.test_endpoint('GET', '/llm-actions/api/llm/providers')
        self.test_endpoint('GET', '/llm-actions/api/llm/actions')
        self.test_endpoint('GET', '/llm-actions/api/step-config/planning/idea/initial_concept')
    
    def test_post_sections_blueprint(self):
        """Test post sections blueprint endpoints"""
        print("\n📝 Testing Post Sections Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/post-sections/test')
        self.test_endpoint('GET', '/post-sections/test-sections')
        self.test_endpoint('GET', '/post-sections/test-minimal')
        
        # Test with post context
        self.test_endpoint('GET', '/post-sections/?post_id=1')
        self.test_endpoint('GET', '/post-sections/sections?post_id=1')
        self.test_endpoint('GET', '/post-sections/sections-summary?post_id=1')
        self.test_endpoint('GET', '/post-sections/sections-images?post_id=1')
    
    def test_post_info_blueprint(self):
        """Test post info blueprint endpoints"""
        print("\n📊 Testing Post Info Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/post-info/')
        self.test_endpoint('GET', '/post-info/health')
        self.test_endpoint('GET', '/post-info/test')
        
        # Test API endpoints
        self.test_endpoint('GET', '/post-info/api/post-info')
        self.test_endpoint('GET', '/post-info/api/post-info/1')
        self.test_endpoint('GET', '/post-info/api/post-info/1/seo')
    
    def test_images_blueprint(self):
        """Test images blueprint endpoints"""
        print("\n🖼️ Testing Images Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/images/test')
        self.test_endpoint('GET', '/images/?post_id=1')
        self.test_endpoint('GET', '/images/upload?post_id=1')
        
        # Test API endpoints
        self.test_endpoint('GET', '/images/api/sections/1')
        self.test_endpoint('GET', '/images/api/images/1')
        self.test_endpoint('GET', '/images/api/images/1/1')
    
    def test_clan_api_blueprint(self):
        """Test clan API blueprint endpoints"""
        print("\n🏪 Testing Clan API Blueprint...")
        
        # Test main routes
        self.test_endpoint('GET', '/clan-api/')
        self.test_endpoint('GET', '/clan-api/test')
        
        # Test API endpoints
        self.test_endpoint('GET', '/clan-api/api/test-product')
        self.test_endpoint('GET', '/clan-api/api/categories')
        self.test_endpoint('GET', '/clan-api/api/products')
        self.test_endpoint('GET', '/clan-api/api/products/1')
        self.test_endpoint('GET', '/clan-api/api/products/1/images')
        self.test_endpoint('GET', '/clan-api/api/products/1/categories')
        self.test_endpoint('GET', '/clan-api/api/products/1/related')
    
    def test_static_assets(self):
        """Test static asset serving"""
        print("\n🎨 Testing Static Assets...")
        
        # Test CSS files
        self.test_endpoint('GET', '/static/css/dist/main.css')
        self.test_endpoint('GET', '/static/workflow_nav/css/nav.dist.css')
        
        # Test images
        self.test_endpoint('GET', '/static/images/site/brand-logo.png')
        
        # Test JS files (if they exist)
        self.test_endpoint('GET', '/static/js/dist/main.js', expected_status=200)
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 404 errors
        self.test_endpoint('GET', '/nonexistent', expected_status=404)
        self.test_endpoint('GET', '/launchpad/nonexistent', expected_status=404)
        self.test_endpoint('GET', '/llm-actions/nonexistent', expected_status=404)
        
        # Test invalid parameters
        self.test_endpoint('GET', '/post-sections/')  # Should require post_id
        self.test_endpoint('GET', '/images/')  # Should require post_id
    
    def test_performance(self):
        """Test basic performance"""
        print("\n⚡ Testing Performance...")
        
        # Test response times for key endpoints
        endpoints_to_test = [
            '/',
            '/launchpad/',
            '/llm-actions/',
            '/post-sections/test',
            '/post-info/test',
            '/images/test',
            '/clan-api/test'
        ]
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            success = self.test_endpoint('GET', endpoint)
            end_time = time.time()
            
            if success:
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                if response_time > 1000:  # More than 1 second
                    print(f"⚠️  Slow response: {endpoint} took {response_time:.2f}ms")
                else:
                    print(f"✅ Fast response: {endpoint} took {response_time:.2f}ms")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Comprehensive Testing of Unified BlogForge Application")
        print("=" * 70)
        
        # Test all blueprints
        self.test_core_blueprint()
        self.test_launchpad_blueprint()
        self.test_llm_actions_blueprint()
        self.test_post_sections_blueprint()
        self.test_post_info_blueprint()
        self.test_images_blueprint()
        self.test_clan_api_blueprint()
        
        # Test additional functionality
        self.test_static_assets()
        self.test_error_handling()
        self.test_performance()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%")
        
        if self.results['errors']:
            print(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"  {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors']) - 10} more errors")
        
        print("\n" + "=" * 70)
        
        # Return success/failure
        return self.results['failed'] == 0

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"Testing unified application at: {base_url}")
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding properly at {base_url}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {base_url}")
        print("Make sure the unified application is running with: python3 unified_app.py")
        sys.exit(1)
    
    # Run tests
    tester = UnifiedAppTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
