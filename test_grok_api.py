#!/usr/bin/env python3
"""
Diagnostic script to test Grok API connection and troubleshoot issues.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('GROK_API_KEY')
base_url = os.getenv('GROK_API_BASE_URL', 'https://api.x.ai/v1')

print("=" * 60)
print("Grok API Diagnostic Tool")
print("=" * 60)

# Check 1: API Key
print("\n1. Checking API Key...")
if not api_key:
    print("   ❌ ERROR: GROK_API_KEY not found in environment variables")
    print("   Please set it in your .env file")
    exit(1)
else:
    print(f"   ✓ API Key found: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
    if api_key.startswith('xai-'):
        print("   ✓ API Key format looks correct (starts with 'xai-')")
    else:
        print("   ⚠️  WARNING: API Key doesn't start with 'xai-' (expected format)")

# Check 2: Base URL
print(f"\n2. Checking Base URL...")
print(f"   URL: {base_url}")

# Check 3: Try API request
print(f"\n3. Testing API Connection...")
print(f"   Endpoint: {base_url}/chat/completions")

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

payload = {
    "model": "grok-beta",
    "messages": [
        {"role": "user", "content": "Say 'Hello' in one word"}
    ],
    "max_tokens": 10
}

try:
    print("   Sending request...")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        print("   ✓ SUCCESS! API is working correctly")
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            print(f"   Response: {content}")
    elif response.status_code == 401:
        print("   ❌ ERROR 401: Unauthorized")
        print("   Your API key is invalid or expired")
        print("   Please check your API key at: https://console.x.ai")
    elif response.status_code == 403:
        print("   ❌ ERROR 403: Forbidden")
        print("   Possible reasons:")
        print("   - API key doesn't have proper permissions")
        print("   - API access not enabled for your account")
        print("   - Incorrect API key format")
        print("   Please verify your API key at: https://console.x.ai")
    elif response.status_code == 404:
        print("   ❌ ERROR 404: Not Found")
        print("   The endpoint URL might be incorrect")
        print("   Try updating GROK_API_BASE_URL in .env")
    else:
        print(f"   ❌ ERROR {response.status_code}")
        print(f"   Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("   ❌ CONNECTION ERROR: Cannot reach the API server")
    print("   Check your internet connection")
except requests.exceptions.Timeout:
    print("   ❌ TIMEOUT ERROR: Request took too long")
    print("   The API server might be slow or unreachable")
except Exception as e:
    print(f"   ❌ UNEXPECTED ERROR: {str(e)}")

print("\n" + "=" * 60)
print("Troubleshooting Steps:")
print("=" * 60)
print("1. Get your API key from: https://console.x.ai")
print("2. Make sure you have API access enabled")
print("3. Check that your API key starts with 'xai-'")
print("4. Update .env file with: GROK_API_KEY=xai-your-key-here")
print("5. For free tier, check rate limits and quotas")
print("=" * 60)
