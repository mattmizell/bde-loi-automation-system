#!/usr/bin/env python3
"""
Test Production Deployment
Verify all services are running correctly in production
"""

import requests
import json
import time
from datetime import datetime

# Production service URLs
SERVICES = {
    "Unified Modular Service": "https://loi-automation-api.onrender.com"
}

def test_service_health(name, base_url):
    """Test service health endpoint"""
    try:
        print(f"\n🔍 Testing {name}...")
        
        # Test health endpoint
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ {name} is healthy")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            return True
        else:
            print(f"❌ {name} health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is not responding (connection error)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name} timed out")
        return False
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return False

def test_api_gateway_routing():
    """Test API Gateway routing functionality"""
    try:
        print(f"\n🔀 Testing API Gateway routing...")
        
        # Test status endpoint
        status_url = f"{SERVICES['Unified Modular Service']}/status"
        response = requests.get(status_url, timeout=15)
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ API Gateway routing is working")
            
            # Check service statuses
            services = status_data.get('services', {})
            for service_name, service_info in services.items():
                status = service_info.get('status', 'unknown')
                response_time = service_info.get('response_time', 'N/A')
                print(f"   {service_name}: {status} ({response_time}ms)")
            
            return True
        else:
            print(f"❌ API Gateway status failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Gateway routing test failed: {e}")
        return False

def test_crm_api():
    """Test CRM API functionality through gateway"""
    try:
        print(f"\n📱 Testing CRM API through gateway...")
        
        # Test contacts endpoint
        contacts_url = f"{SERVICES['Unified Modular Service']}/api/contacts?limit=5"
        headers = {
            "Authorization": "ApiKey loi-service-key",
            "Content-Type": "application/json"
        }
        
        response = requests.get(contacts_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            contacts_data = response.json()
            contact_count = len(contacts_data.get('contacts', []))
            total = contacts_data.get('total', 0)
            print(f"✅ CRM API is working")
            print(f"   Retrieved {contact_count} contacts (total: {total})")
            return True
        else:
            print(f"❌ CRM API test failed: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ CRM API test failed: {e}")
        return False

def test_search_functionality():
    """Test search functionality"""
    try:
        print(f"\n🔍 Testing search functionality...")
        
        search_url = f"{SERVICES['Unified Modular Service']}/api/search_contacts"
        headers = {
            "Authorization": "ApiKey loi-service-key",
            "Content-Type": "application/json"
        }
        
        search_data = {
            "query": "fuel",
            "limit": 3
        }
        
        response = requests.post(search_url, headers=headers, json=search_data, timeout=10)
        
        if response.status_code == 200:
            search_results = response.json()
            results_count = len(search_results.get('results', []))
            print(f"✅ Search functionality is working")
            print(f"   Found {results_count} results for 'fuel'")
            return True
        else:
            print(f"❌ Search test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 Testing Better Day Energy Production Deployment")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test individual service health
    for name, url in SERVICES.items():
        results[f"{name}_health"] = test_service_health(name, url)
    
    # Test API Gateway functionality
    results["gateway_routing"] = test_api_gateway_routing()
    
    # Test CRM API
    results["crm_api"] = test_crm_api()
    
    # Test search
    results["search"] = test_search_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is successful!")
        print("\n📋 Ready for production use:")
        print(f"   Unified Service: {SERVICES['Unified Modular Service']}")
        print(f"   Status Dashboard: {SERVICES['Unified Modular Service']}/status")
        return True
    else:
        print("⚠️  Some tests failed. Check service logs in Render dashboard.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)