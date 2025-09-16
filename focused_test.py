#!/usr/bin/env python3
"""
Focused test for review request requirements
"""

import requests
import json
import sys

def test_houses_endpoint():
    """Test the specific requirements from review request"""
    base_url = "https://vasdom-crm.preview.emergentagent.com"
    
    print("🎯 FOCUSED TEST - Review Request Requirements")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: GET /api/cleaning/houses with filters
    print("\n1️⃣ Testing GET /api/cleaning/houses with filters...")
    
    test_cases = [
        {"name": "Brigade filter", "params": {"brigade": "4 бригада", "limit": 10}},
        {"name": "Management company filter", "params": {"management_company": "УК", "limit": 10}},
        {"name": "Cleaning date filter", "params": {"cleaning_date": "2025-09-05", "limit": 10}},
        {"name": "Date range filter", "params": {"date_from": "2025-09-01", "date_to": "2025-09-30", "limit": 10}},
        {"name": "Basic pagination", "params": {"limit": 5, "page": 1}},
    ]
    
    for test_case in test_cases:
        tests_total += 1
        try:
            response = requests.get(f"{base_url}/api/cleaning/houses", params=test_case["params"], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response schema: { houses: [...], total, page, limit, pages }
                required_fields = ['houses', 'total', 'page', 'limit', 'pages']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Verify integers for total/page/limit/pages
                    integer_fields = ['total', 'page', 'limit', 'pages']
                    all_integers = all(isinstance(data[field], int) for field in integer_fields)
                    
                    if all_integers and isinstance(data['houses'], list):
                        print(f"   ✅ {test_case['name']}: Schema valid, {len(data['houses'])} houses")
                        tests_passed += 1
                        
                        # Check house object schema if houses exist
                        if data['houses']:
                            house = data['houses'][0]
                            required_house_fields = ['id', 'title', 'address', 'brigade', 'management_company', 'periodicity', 'cleaning_dates', 'bitrix_url']
                            missing_house_fields = [field for field in required_house_fields if field not in house]
                            
                            if not missing_house_fields:
                                # Verify field types
                                type_checks = [
                                    isinstance(house['brigade'], str),
                                    isinstance(house['management_company'], str),
                                    isinstance(house['periodicity'], str),
                                    isinstance(house['cleaning_dates'], dict),
                                    isinstance(house['bitrix_url'], str)
                                ]
                                
                                if all(type_checks):
                                    print(f"      House schema valid: brigade='{house['brigade']}', mc='{house['management_company']}'")
                                else:
                                    print(f"      ⚠️ House type validation failed")
                            else:
                                print(f"      ⚠️ Missing house fields: {missing_house_fields}")
                    else:
                        print(f"   ❌ {test_case['name']}: Schema validation failed")
                else:
                    print(f"   ❌ {test_case['name']}: Missing fields: {missing_fields}")
            else:
                print(f"   ❌ {test_case['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['name']}: Error - {e}")
    
    # Test 2: GET /api/cleaning/house/{id}/details
    print("\n2️⃣ Testing GET /api/cleaning/house/{id}/details...")
    
    # First get a house ID
    try:
        response = requests.get(f"{base_url}/api/cleaning/houses", params={"limit": 1}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('houses'):
                house_id = data['houses'][0]['id']
                print(f"   Using house ID: {house_id}")
                
                # Test valid house details
                tests_total += 1
                response = requests.get(f"{base_url}/api/cleaning/house/{house_id}/details", timeout=30)
                
                if response.status_code == 200:
                    details = response.json()
                    if 'house' in details and 'bitrix_url' in details['house']:
                        bitrix_url = details['house']['bitrix_url']
                        if isinstance(bitrix_url, str):
                            print(f"   ✅ House details valid: bitrix_url present ({len(bitrix_url)} chars)")
                            tests_passed += 1
                        else:
                            print(f"   ❌ bitrix_url should be string, got {type(bitrix_url)}")
                    else:
                        print(f"   ❌ Missing house.bitrix_url in response")
                else:
                    print(f"   ❌ House details HTTP {response.status_code}")
                
                # Test invalid house ID (should be 404, not 500)
                tests_total += 1
                response = requests.get(f"{base_url}/api/cleaning/house/999999/details", timeout=30)
                
                if response.status_code == 404:
                    print(f"   ✅ Invalid ID correctly returns 404")
                    tests_passed += 1
                elif response.status_code == 500:
                    print(f"   ❌ Invalid ID returns 500 (should be 404)")
                else:
                    print(f"   ❌ Invalid ID returns {response.status_code} (expected 404)")
            else:
                print("   ❌ No houses available for testing")
        else:
            print(f"   ❌ Failed to get houses for ID: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ House details test error: {e}")
    
    # Test 3: Bitrix fallback behavior
    print("\n3️⃣ Testing Bitrix 503 fallback behavior...")
    
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/cleaning/houses", params={"limit": 5}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Should have correct shape even if Bitrix is down
            if isinstance(data, dict) and 'houses' in data and isinstance(data['houses'], list):
                print(f"   ✅ Houses endpoint stable: {len(data['houses'])} houses, total={data.get('total', 'N/A')}")
                tests_passed += 1
            else:
                print(f"   ❌ Invalid response structure")
        elif response.status_code == 500:
            print(f"   ❌ Houses endpoint returns 500 (should handle Bitrix failures gracefully)")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Bitrix fallback test error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FOCUSED TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 ALL REVIEW REQUEST REQUIREMENTS PASSED!")
        return True
    else:
        print("⚠️ Some requirements need attention")
        return False

if __name__ == "__main__":
    success = test_houses_endpoint()
    sys.exit(0 if success else 1)