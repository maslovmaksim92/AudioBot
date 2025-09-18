#!/usr/bin/env python3
"""
Test specific diagnostics endpoints for review request
"""

import requests
import json
import sys
from datetime import datetime

def test_diagnostics_endpoints():
    """Test the two specific diagnostics endpoints"""
    base_url = "https://audiobot-qci2.onrender.com"
    
    print("🔍 REVIEW REQUEST DIAGNOSTICS TESTING")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print("Testing specific diagnostics endpoints:")
    print("1) GET /api/ai-knowledge/db-dsn")
    print("2) GET /api/ai-knowledge/db-check")
    print("-" * 70)
    
    results = {}
    
    # Test 1: GET /api/ai-knowledge/db-dsn
    print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
    try:
        response = requests.get(f"{base_url}/api/ai-knowledge/db-dsn", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Status 200")
            print("📄 Full JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Extract specific fields mentioned in review request
            raw_present = data.get('raw_present', 'N/A')
            raw_contains_sslmode = data.get('raw_contains_sslmode', 'N/A')
            raw = data.get('raw', {})
            normalized = data.get('normalized', {})
            
            print(f"\n🔍 Key Fields:")
            print(f"   raw_present: {raw_present}")
            print(f"   raw_contains_sslmode: {raw_contains_sslmode}")
            print(f"   raw.scheme: {raw.get('scheme', 'N/A')}")
            print(f"   raw.query: {raw.get('query', 'N/A')}")
            print(f"   normalized.query: {normalized.get('query', 'N/A')}")
            
            results['db-dsn'] = {'success': True, 'data': data}
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error: {response.text}")
            results['db-dsn'] = {'success': False, 'status': response.status_code}
            
    except Exception as e:
        print(f"❌ EXCEPTION - {str(e)}")
        results['db-dsn'] = {'success': False, 'error': str(e)}
    
    # Test 2: GET /api/ai-knowledge/db-check
    print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
    try:
        response = requests.get(f"{base_url}/api/ai-knowledge/db-check", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Status 200")
            print("📄 Full JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            results['db-check'] = {'success': True, 'data': data}
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error: {response.text}")
            results['db-check'] = {'success': False, 'status': response.status_code}
            
    except Exception as e:
        print(f"❌ EXCEPTION - {str(e)}")
        results['db-check'] = {'success': False, 'error': str(e)}
    
    # Summary
    print("\n📋 REVIEW REQUEST RESULTS SUMMARY:")
    print("=" * 50)
    
    dsn_success = results.get('db-dsn', {}).get('success', False)
    check_success = results.get('db-check', {}).get('success', False)
    
    if dsn_success:
        print("✅ db-dsn endpoint: WORKING")
    else:
        print("❌ db-dsn endpoint: FAILED")
        
    if check_success:
        print("✅ db-check endpoint: WORKING")
    else:
        print("❌ db-check endpoint: FAILED")
    
    print(f"\nOverall Success: {dsn_success and check_success}")
    
    return results

if __name__ == "__main__":
    print("🚀 VasDom AudioBot Backend Testing - REVIEW REQUEST DIAGNOSTICS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = test_diagnostics_endpoints()
    
    # Return both JSON responses as requested
    print("\n" + "=" * 60)
    print("CAPTURED JSON RESPONSES FOR REVIEW REQUEST:")
    print("=" * 60)
    
    if 'db-dsn' in results and results['db-dsn'].get('success'):
        print("\n1) GET /api/ai-knowledge/db-dsn Response:")
        print(json.dumps(results['db-dsn']['data'], indent=2, ensure_ascii=False))
    
    if 'db-check' in results and results['db-check'].get('success'):
        print("\n2) GET /api/ai-knowledge/db-check Response:")
        print(json.dumps(results['db-check']['data'], indent=2, ensure_ascii=False))
    
    # Exit with success code if both endpoints worked
    dsn_success = results.get('db-dsn', {}).get('success', False)
    check_success = results.get('db-check', {}).get('success', False)
    sys.exit(0 if (dsn_success and check_success) else 1)