#!/usr/bin/env python3
"""
Debug script to check Bitrix24 users data structure
"""
import asyncio
import sys
import os
sys.path.append('/app/backend')

from app.services.bitrix_service import BitrixService
from app.config.settings import BITRIX24_WEBHOOK_URL

async def debug_users():
    """Debug users data from Bitrix24"""
    try:
        print(f"🔍 Debugging users from Bitrix24...")
        print(f"🔗 Webhook URL: {BITRIX24_WEBHOOK_URL[:50]}...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        users = await bitrix.get_users()
        
        print(f"📊 Total users retrieved: {len(users)}")
        
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
            print("❌ No users retrieved")
            
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_users())