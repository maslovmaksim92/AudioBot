#!/usr/bin/env python3
"""
Debug script to check Bitrix24 users data structure
"""
import asyncio
import sys
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

BITRIX24_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')

async def debug_users_direct():
    """Debug users data directly from Bitrix24 API"""
    try:
        print(f"🔍 Debugging users directly from Bitrix24 API...")
        print(f"🔗 Webhook URL: {BITRIX24_WEBHOOK_URL}")
        
        url = f"{BITRIX24_WEBHOOK_URL}user.get.json"
        print(f"🔗 Full URL: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Response keys: {list(data.keys())}")
                
                if 'result' in data:
                    users = data['result']
                    print(f"📊 Total users in result: {len(users)}")
                    
                    if len(users) > 0:
                        print(f"\n📋 Sample user data structure:")
                        sample_user = users[0]
                        for key, value in sample_user.items():
                            print(f"   {key}: {value}")
                        
                        print(f"\n📊 Active status analysis:")
                        active_statuses = {}
                        for user in users:
                            active_status = user.get('ACTIVE', 'UNKNOWN')
                            active_statuses[active_status] = active_statuses.get(active_status, 0) + 1
                        
                        print(f"   Active statuses: {active_statuses}")
                        
                        # Check for users with ACTIVE = 'Y'
                        active_users = [u for u in users if u.get('ACTIVE') == 'Y']
                        print(f"   Users with ACTIVE='Y': {len(active_users)}")
                        
                        # Check for users with names
                        users_with_names = [u for u in users if u.get('NAME') or u.get('LAST_NAME')]
                        print(f"   Users with names: {len(users_with_names)}")
                        
                        if len(active_users) > 0:
                            print(f"\n📋 Sample active user:")
                            active_user = active_users[0]
                            print(f"   ID: {active_user.get('ID')}")
                            print(f"   NAME: {active_user.get('NAME')}")
                            print(f"   LAST_NAME: {active_user.get('LAST_NAME')}")
                            print(f"   EMAIL: {active_user.get('EMAIL')}")
                            print(f"   WORK_POSITION: {active_user.get('WORK_POSITION')}")
                            print(f"   ACTIVE: {active_user.get('ACTIVE')}")
                    else:
                        print("❌ No users in result array")
                else:
                    print("❌ No 'result' key in response")
                    print(f"📊 Full response: {data}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"📊 Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_users_direct())