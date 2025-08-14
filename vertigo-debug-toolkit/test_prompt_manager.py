#\!/usr/bin/env python3
"""
Test script to verify the prompt manager functionality
"""
import requests
import json

def test_prompt_manager():
    base_url = "http://localhost:5001"
    
    print("=== Testing Prompt Manager ===")
    
    # Test 1: Can we access the manager page?
    print("\n1. Testing manager page access...")
    try:
        response = requests.get(f"{base_url}/prompts/manager")
        print(f"Manager page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Manager page accessible")
        else:
            print(f"❌ Manager page error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Manager page error: {e}")
        return False
    
    # Test 2: Can we access the API endpoint?
    print("\n2. Testing API endpoint...")
    try:
        response = requests.get(f"{base_url}/prompts/api/prompts/list")
        print(f"API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working - Found {len(data['data'])} prompts")
            
            # Show sample data
            if data['data']:
                sample = data['data'][0]
                print(f"Sample prompt: {sample['name']} (v{sample['version']})")
                print(f"Tags: {sample['tags']}")
                print(f"Active: {sample['is_active']}")
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False

if __name__ == "__main__":
    success = test_prompt_manager()
    if success:
        print("\n🎉 Backend is working correctly\!")
        print("The issue is likely in the frontend JavaScript.")
        print("\nNext steps:")
        print("1. Check browser console for JavaScript errors")
        print("2. Check if authentication is required")
        print("3. Verify the page loads the JavaScript properly")
    else:
        print("\n❌ Backend has issues that need to be fixed first.")
