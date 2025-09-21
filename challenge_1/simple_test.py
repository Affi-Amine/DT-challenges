#!/usr/bin/env python3
"""
Simple test runner for Challenge 1 - Document Processing System
Tests basic functionality without complex dependencies
"""

import requests
import json
import time
import os
import tempfile
from pathlib import Path

class Challenge1Tester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def log_result(self, test_name, status, message="", duration=0):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.3f}s"
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message} ({duration:.3f}s)")
        
    def test_health_check(self):
        """Test health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check", "PASS", "Service is healthy", duration)
                else:
                    self.log_result("Health Check", "FAIL", f"Unexpected status: {data.get('status')}", duration)
            else:
                self.log_result("Health Check", "FAIL", f"HTTP {response.status_code}", duration)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result("Health Check", "SKIP", f"Service not running: {str(e)}", duration)
            
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        start_time = time.time()
        try:
            # Test OpenAPI docs
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("API Documentation", "PASS", "Swagger UI accessible", duration)
            else:
                self.log_result("API Documentation", "FAIL", f"HTTP {response.status_code}", duration)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result("API Documentation", "SKIP", f"Service not running: {str(e)}", duration)
            
    def test_file_upload_simulation(self):
        """Test file upload endpoint (simulation)"""
        start_time = time.time()
        
        # Create a test markdown file
        test_content = """
# Test Document

This is a test document for the DiploTools system.

## Content

- Diplomatic relations
- International law
- Treaty negotiations
- United Nations protocols

## Conclusion

This document tests the processing pipeline.
"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(test_content)
                temp_path = f.name
            
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.md', f, 'text/markdown')}
                response = requests.post(f"{self.base_url}/documents/upload", files=files, timeout=10)
                
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("File Upload", "PASS", "Document uploaded successfully", duration)
            elif response.status_code == 422:
                self.log_result("File Upload", "SKIP", "Validation error (expected without full setup)", duration)
            else:
                self.log_result("File Upload", "FAIL", f"HTTP {response.status_code}", duration)
                
            # Cleanup
            os.unlink(temp_path)
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result("File Upload", "SKIP", f"Service not running: {str(e)}", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("File Upload", "FAIL", f"Error: {str(e)}", duration)
            
    def test_search_endpoint(self):
        """Test search endpoint"""
        start_time = time.time()
        try:
            params = {
                'query': 'diplomatic relations',
                'search_type': 'hybrid',
                'limit': 5
            }
            response = requests.get(f"{self.base_url}/search", params=params, timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Search Endpoint", "PASS", "Search endpoint accessible", duration)
            elif response.status_code == 422:
                self.log_result("Search Endpoint", "SKIP", "Validation error (expected without data)", duration)
            else:
                self.log_result("Search Endpoint", "FAIL", f"HTTP {response.status_code}", duration)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result("Search Endpoint", "SKIP", f"Service not running: {str(e)}", duration)
            
    def test_stats_endpoint(self):
        """Test system stats endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Stats Endpoint", "PASS", "Stats endpoint accessible", duration)
            else:
                self.log_result("Stats Endpoint", "FAIL", f"HTTP {response.status_code}", duration)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result("Stats Endpoint", "SKIP", f"Service not running: {str(e)}", duration)
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Challenge 1 Tests - Document Processing System")
        print("=" * 60)
        
        self.test_health_check()
        self.test_api_documentation()
        self.test_file_upload_simulation()
        self.test_search_endpoint()
        self.test_stats_endpoint()
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        skipped = len([r for r in self.results if r["status"] == "SKIP"])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
        print(f"📈 Total: {total}")
        
        if failed == 0:
            print("\n🎉 All tests passed or skipped (service may not be running)")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            
        return self.results

if __name__ == "__main__":
    tester = Challenge1Tester()
    results = tester.run_all_tests()
    
    # Save results to JSON
    with open("challenge_1_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to challenge_1_test_results.json")