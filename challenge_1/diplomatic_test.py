#!/usr/bin/env python3
"""
Comprehensive test script for diplomatic data in Challenge 1
Tests various diplomatic scenarios and search queries
"""

import requests
import json
import time
from typing import Dict, List

BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Test an API endpoint and return the response"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        response.raise_for_status()
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }

def run_diplomatic_tests():
    """Run comprehensive diplomatic data tests"""
    print("🏛️  DiploTools Diplomatic Data Testing Suite")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. 🔍 Health Check")
    result = test_api_endpoint("/health")
    if result["success"]:
        print(f"✅ API is healthy: {result['data']['status']}")
    else:
        print(f"❌ Health check failed: {result['error']}")
        return
    
    # Test 2: Basic Search Queries
    diplomatic_queries = [
        {
            "name": "Diplomatic Immunity",
            "query": "diplomatic immunity",
            "expected_docs": ["doc_1", "doc_3"]
        },
        {
            "name": "Trade Relations", 
            "query": "trade agreements",
            "expected_docs": ["doc_4"]
        },
        {
            "name": "Vienna Convention",
            "query": "Vienna Convention",
            "expected_docs": ["doc_3"]
        },
        {
            "name": "Consular Services",
            "query": "consular services passport",
            "expected_docs": ["doc_6"]
        },
        {
            "name": "Peace Negotiations",
            "query": "peace negotiation mediation",
            "expected_docs": ["doc_7"]
        },
        {
            "name": "Cultural Diplomacy",
            "query": "cultural exchange programs",
            "expected_docs": ["doc_8"]
        },
        {
            "name": "Climate Diplomacy",
            "query": "climate change negotiations",
            "expected_docs": ["doc_9"]
        },
        {
            "name": "Economic Sanctions",
            "query": "economic sanctions",
            "expected_docs": ["doc_11"]
        }
    ]
    
    print("\n2. 🔍 Diplomatic Search Queries")
    for i, query_test in enumerate(diplomatic_queries, 1):
        print(f"\n   {i}. Testing: {query_test['name']}")
        
        # Test POST search
        search_data = {
            "query": query_test["query"],
            "search_type": "hybrid",
            "limit": 5
        }
        
        result = test_api_endpoint("/search", "POST", search_data)
        if result["success"]:
            data = result["data"]
            found_docs = [doc["id"] for doc in data["results"]]
            print(f"      Query: '{query_test['query']}'")
            print(f"      Results: {data['total_results']} documents found")
            print(f"      Document IDs: {found_docs}")
            
            # Check if expected documents are found
            expected_found = any(doc_id in found_docs for doc_id in query_test["expected_docs"])
            if expected_found:
                print(f"      ✅ Expected documents found")
            else:
                print(f"      ⚠️  Expected documents not found: {query_test['expected_docs']}")
        else:
            print(f"      ❌ Search failed: {result['error']}")
    
    # Test 3: Country-specific searches
    print("\n3. 🌍 Country-specific Searches")
    country_queries = [
        {"country": "Tunisia", "query": "Tunisia"},
        {"country": "France", "query": "France"},
        {"country": "Germany", "query": "Germany"},
        {"country": "International", "query": "international"}
    ]
    
    for query_test in country_queries:
        result = test_api_endpoint("/search", "POST", {
            "query": query_test["query"],
            "search_type": "hybrid",
            "limit": 10
        })
        
        if result["success"]:
            data = result["data"]
            print(f"   {query_test['country']}: {data['total_results']} documents")
        else:
            print(f"   {query_test['country']}: Search failed")
    
    # Test 4: Document Type Searches
    print("\n4. 📄 Document Type Searches")
    type_queries = [
        {"type": "treaty", "query": "treaty"},
        {"type": "policy", "query": "policy"},
        {"type": "economic", "query": "economic"},
        {"type": "diplomatic", "query": "diplomatic"}
    ]
    
    for query_test in type_queries:
        result = test_api_endpoint("/search", "POST", {
            "query": query_test["query"],
            "search_type": "hybrid",
            "limit": 10
        })
        
        if result["success"]:
            data = result["data"]
            print(f"   {query_test['type'].title()}: {data['total_results']} documents")
        else:
            print(f"   {query_test['type'].title()}: Search failed")
    
    # Test 5: GET endpoint search
    print("\n5. 🔗 GET Search Endpoint")
    result = test_api_endpoint("/search?query=diplomatic&search_type=hybrid&limit=3")
    if result["success"]:
        data = result["data"]
        print(f"   ✅ GET search successful: {data['total_results']} results")
    else:
        print(f"   ❌ GET search failed: {result['error']}")
    
    # Test 6: Statistics
    print("\n6. 📊 System Statistics")
    result = test_api_endpoint("/stats")
    if result["success"]:
        stats = result["data"]
        print(f"   Total Documents: {stats.get('total_documents', 'N/A')}")
        print(f"   Total Chunks: {stats.get('total_chunks', 'N/A')}")
        print(f"   Database Size: {stats.get('database_size', 'N/A')}")
        print(f"   Cache Hit Rate: {stats.get('cache_hit_rate', 'N/A')}")
        print(f"   System Health: {stats.get('system_health', 'N/A')}")
        print(f"   Uptime: {stats.get('uptime', 'N/A')}")
    else:
        print(f"   ❌ Stats failed: {result['error']}")
    
    # Test 7: Document Listing
    print("\n7. 📋 Document Listing")
    result = test_api_endpoint("/documents?limit=5")
    if result["success"]:
        data = result["data"]
        print(f"   ✅ Listed {len(data['documents'])} documents")
        print(f"   Total available: {data['total']}")
    else:
        print(f"   ❌ Document listing failed: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🎉 Diplomatic data testing completed!")
    print("💡 Use the curl commands below to test manually")

def generate_curl_commands():
    """Generate curl commands for manual testing"""
    print("\n🔧 CURL Commands for Manual Testing:")
    print("=" * 50)
    
    curl_commands = [
        {
            "name": "Health Check",
            "command": "curl -X GET http://localhost:8000/health"
        },
        {
            "name": "Search for Diplomatic Immunity",
            "command": '''curl -X POST http://localhost:8000/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "diplomatic immunity", "search_type": "hybrid", "limit": 5}' '''
        },
        {
            "name": "Search for Trade Relations",
            "command": '''curl -X POST http://localhost:8000/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "trade agreements Tunisia", "search_type": "hybrid", "limit": 3}' '''
        },
        {
            "name": "Search for Vienna Convention",
            "command": '''curl -X POST http://localhost:8000/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Vienna Convention 1961", "search_type": "semantic", "limit": 2}' '''
        },
        {
            "name": "Search for Peace Negotiations",
            "command": '''curl -X POST http://localhost:8000/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "peace mediation conflict", "search_type": "keyword", "limit": 3}' '''
        },
        {
            "name": "GET Search (URL params)",
            "command": "curl -X GET 'http://localhost:8000/search?query=consular%20services&search_type=hybrid&limit=3'"
        },
        {
            "name": "System Statistics",
            "command": "curl -X GET http://localhost:8000/stats"
        },
        {
            "name": "List Documents",
            "command": "curl -X GET 'http://localhost:8000/documents?limit=10&offset=0'"
        },
        {
            "name": "Upload Document (example)",
            "command": '''curl -X POST http://localhost:8000/documents/upload \\
  -F "file=@sample_diplomatic_doc.txt" '''
        }
    ]
    
    for i, cmd in enumerate(curl_commands, 1):
        print(f"\n{i}. {cmd['name']}:")
        print(f"   {cmd['command']}")
    
    print(f"\n💡 Pro tip: Add ' | jq .' to any curl command for pretty JSON formatting")
    print(f"   Example: curl -X GET http://localhost:8000/health | jq .")

if __name__ == "__main__":
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run the tests
    run_diplomatic_tests()
    
    # Generate curl commands
    generate_curl_commands()