#!/usr/bin/env python3
"""
Simple test to check what's happening with Bitrix24 API
"""

import requests
import json

def test_simple_endpoints():
    base_url = "https://autobot-learning.preview.emergentagent.com/api"
    
    print("🔍 Testing simple endpoints...")
    
    # Test bitrix24/test
    try:
        response = requests.get(f"{base_url}/bitrix24/test", timeout=10)
        print(f"Bitrix24 test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Bitrix24 test error: {e}")
    
    print("\n" + "="*50)
    
    # Test cleaning/houses
    try:
        response = requests.get(f"{base_url}/cleaning/houses", timeout=10)
        print(f"Cleaning houses: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Houses count: {len(data.get('houses', []))}")
            print(f"Total in system: {data.get('total_in_system', 'N/A')}")
            print(f"Source: {data.get('source', 'N/A')}")
            if data.get('houses'):
                print(f"First house: {json.dumps(data['houses'][0], indent=2)}")
    except Exception as e:
        print(f"Cleaning houses error: {e}")

if __name__ == "__main__":
    test_simple_endpoints()