import requests
import sys
import time

def verify_endpoints():
    print("=======================================")
    print("🔍 Mahoraga Space Endpoint Verification")
    print("=======================================\n")
    
    BASE_URL = "http://localhost:7860"
    all_passed = True

    # 1. Test Frontend Serve
    print("1️⃣  Testing Frontend Catch-all Route (/) ...", end=" ")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200 and "<html" in response.text.lower():
            print("✅ PASSED")
        else:
            print(f"❌ FAILED (Status: {response.status_code}, Is HTML: {'<html' in response.text.lower()})")
            all_passed = False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED (Connection Error: {e})")
        all_passed = False

    # 2. Test Backend API (/api/model-status)
    print("2️⃣  Testing Backend API (/api/model-status) ...", end=" ")
    try:
        response = requests.get(f"{BASE_URL}/api/model-status", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ PASSED")
            except ValueError:
                print("❌ FAILED (Did not return valid JSON)")
                all_passed = False
        else:
            print(f"❌ FAILED (Status: {response.status_code})")
            all_passed = False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED (Connection Error: {e})")
        all_passed = False
        
    # 3. Test React Router Fallback (/some-random-path)
    print("3️⃣  Testing React Router Fallback (/random-path) ...", end=" ")
    try:
        response = requests.get(f"{BASE_URL}/random-path", timeout=5)
        if response.status_code == 200 and "<html" in response.text.lower():
            print("✅ PASSED")
        else:
            print(f"❌ FAILED (Status: {response.status_code})")
            all_passed = False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED (Connection Error: {e})")
        all_passed = False

    print("\n=======================================")
    if all_passed:
        print("🎉 ALL TESTS PASSED! Your Space is ready.")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    verify_endpoints()
