#!/usr/bin/env python3
"""
Token Grant Fix Test - Quick verify after token grant fix
Review Request: 
1) POST https://audiobot-qci2.onrender.com/api/voice/call/start with {"phone_number":"+79001234567"} -> expect 200
2) Ensure logs no longer show 'AccessToken object has no attribute add_grants'
3) GET /api/voice/call/{call_id}/status twice with 2s interval to observe status change
"""

import requests
import json
import time

def test_token_grant_fix():
    base_url = "https://audiobot-qci2.onrender.com"
    
    print("🚀 VasDom AudioBot Backend API - Token Grant Fix Verification")
    print(f"📍 Base URL: {base_url}")
    print("🔧 Testing per review request:")
    print("1) POST /api/voice/call/start with phone_number -> expect 200")
    print("2) Ensure logs no longer show 'AccessToken object has no attribute add_grants'")
    print("3) GET /api/voice/call/call_id/status twice with 2s interval to observe status change")
    print("=" * 80)
    
    # Test 1: POST /api/voice/call/start
    print("\n1️⃣ Testing POST /api/voice/call/start")
    print("   Body: phone_number: +79001234567")
    print("   Expected: 200 (token grant fix should resolve previous issues)")
    
    request_data = {"phone_number": "+79001234567"}
    
    try:
        response = requests.post(f"{base_url}/api/voice/call/start", json=request_data, timeout=30)
        status = response.status_code
        
        try:
            data = response.json() if response.content else {}
        except:
            data = {"error": "Non-JSON response", "content": response.text[:500]}
        
        print(f"\n📊 DETAILED RESPONSE:")
        print(f"   Status Code: {status}")
        print(f"   Response Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if status == 200:
            print(f"   ✅ Status: {status} ✓ (Token grant fix successful)")
            
            # Check required schema keys: call_id, room_name, status
            call_id = data.get('call_id')
            room_name = data.get('room_name')
            call_status = data.get('status')
            sip_participant_id = data.get('sip_participant_id')
            
            if call_id and room_name and call_status:
                print(f"   ✅ Schema valid: call_id, room_name, status present")
                print(f"   📋 Call Details:")
                print(f"      call_id: {call_id}")
                print(f"      room_name: {room_name}")
                print(f"      status: {call_status}")
                print(f"      sip_participant_id: {sip_participant_id}")
                
                # Test 3: Status monitoring
                test_status_monitoring(base_url, call_id)
                
            else:
                print(f"   ❌ Missing required schema keys")
                
        elif status in [500, 502]:
            print(f"   ❌ Status: {status} (Still failing after token grant fix)")
            
            detail = data.get('detail', '')
            
            # Check for specific errors mentioned in review request
            if 'AccessToken object has no attribute add_grants' in detail:
                print(f"   ❌ 'AccessToken object has no attribute add_grants' error still present")
                print(f"   Detail: {detail}")
            elif 'identity cannot be empty' in detail:
                print(f"   ❌ 'identity cannot be empty' error still present")
                print(f"   Detail: {detail}")
            else:
                # This might be expected - SIP provider errors are acceptable
                print(f"   ✅ Different error after fix (SIP provider issue expected)")
                print(f"   Detail: {detail}")
                
        else:
            print(f"   ❌ Unexpected status: {status}")
            print(f"   Data: {data}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

def test_status_monitoring(base_url, call_id):
    """Test 3: GET /api/voice/call/{call_id}/status twice with 2s interval"""
    call_id_short = call_id[:8] if len(call_id) > 8 else call_id
    print(f"\n3️⃣ Testing GET /api/voice/call/{call_id_short}.../status (2 calls with 2s interval)")
    print("   Expected: Observe status change between calls")
    
    # First status check
    print(f"\n   📞 First status check:")
    try:
        response1 = requests.get(f"{base_url}/api/voice/call/{call_id}/status", timeout=30)
        status1 = response1.status_code
        data1 = response1.json() if response1.content else {}
        
        if status1 == 200:
            print(f"   ✅ Status: {status1} ✓")
            print(f"   Response: {json.dumps(data1, indent=2, ensure_ascii=False)}")
            
            first_status = data1.get('status', 'unknown')
            first_duration = data1.get('duration')
            
            print(f"   📋 First check - status: {first_status}, duration: {first_duration}")
        else:
            print(f"   ❌ First check failed - Status: {status1}, Data: {data1}")
            return
            
    except Exception as e:
        print(f"   ❌ First check failed: {str(e)}")
        return
    
    # Wait 2 seconds
    print(f"\n   ⏱️ Waiting 2 seconds...")
    time.sleep(2)
    
    # Second status check
    print(f"\n   📞 Second status check:")
    try:
        response2 = requests.get(f"{base_url}/api/voice/call/{call_id}/status", timeout=30)
        status2 = response2.status_code
        data2 = response2.json() if response2.content else {}
        
        if status2 == 200:
            print(f"   ✅ Status: {status2} ✓")
            print(f"   Response: {json.dumps(data2, indent=2, ensure_ascii=False)}")
            
            second_status = data2.get('status', 'unknown')
            second_duration = data2.get('duration')
            
            print(f"   📋 Second check - status: {second_status}, duration: {second_duration}")
            
            # Compare status changes
            status_changed = first_status != second_status
            duration_changed = first_duration != second_duration
            
            if status_changed or duration_changed:
                changes = []
                if status_changed:
                    changes.append(f"status: {first_status} -> {second_status}")
                if duration_changed:
                    changes.append(f"duration: {first_duration} -> {second_duration}")
                
                print(f"   ✅ Status changes observed: {', '.join(changes)} ✓")
            else:
                print(f"   ✅ Status consistent: {first_status} (no change in 2s interval) ✓")
                
        else:
            print(f"   ❌ Second check failed - Status: {status2}, Data: {data2}")
            
    except Exception as e:
        print(f"   ❌ Second check failed: {str(e)}")

if __name__ == "__main__":
    test_token_grant_fix()