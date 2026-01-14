#!/usr/bin/env python3
"""
Diagnostic script to test Mistral AI API connection and troubleshoot issues.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('MISTRAL_API_KEY')
base_url = os.getenv('MISTRAL_API_BASE_URL', 'https://api.mistral.ai/v1')
model = os.getenv('MISTRAL_MODEL', 'open-mistral-nemo')

print("=" * 60)
print("Mistral AI API Diagnostic Tool")
print("=" * 60)

# Check 1: API Key
print("\n1. Checking API Key...")
if not api_key:
    print("   ❌ ERROR: MISTRAL_API_KEY not found in environment variables")
    print("   Please set it in your .env file")
    exit(1)
else:
    print(f"   ✓ API Key found: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")

# Check 2: Base URL
print(f"\n2. Checking Base URL...")
print(f"   URL: {base_url}")
print(f"   Model: {model}")

# Check 3: Try API request
print(f"\n3. Testing API Connection...")
print(f"   Endpoint: {base_url}/chat/completions")

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

payload = {
    "model": model,
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
            print(f"\n   ✓ Mistral AI is ready to use!")
    elif response.status_code == 401:
        print("   ❌ ERROR 401: Unauthorized")
        print("   Your API key is invalid or expired")
        print("   Please check your API key at: https://console.mistral.ai")
    elif response.status_code == 403:
        print("   ❌ ERROR 403: Forbidden")
        print("   Possible reasons:")
        print("   - API key doesn't have proper permissions")
        print("   - API access not enabled for your account")
        print("   - Free tier limits exceeded")
        print("   Please verify your API key at: https://console.mistral.ai")
    elif response.status_code == 404:
        print("   ❌ ERROR 404: Not Found")
        print("   The endpoint URL or model might be incorrect")
        print("   Current model: " + model)
        print("   Try updating MISTRAL_MODEL in .env to: mistral-small-latest")
    elif response.status_code == 429:
        print("   ❌ ERROR 429: Rate Limit Exceeded")
        print("   You've hit the free tier rate limits")
        print("   Wait a moment and try again, or upgrade at: https://console.mistral.ai")
    else:
        print(f"   ❌ ERROR {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Response: {error_data}")
        except:
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
print("1. Get your API key from: https://console.mistral.ai")
print("2. Click on 'API Keys' in the left sidebar")
print("3. Create a new API key if you don't have one")
print("4. Update .env file with: MISTRAL_API_KEY=your-key-here")
print("5. Mistral offers 1 billion tokens/month on free tier!")
print("6. Recommended free model: open-mistral-nemo")
print("=" * 60)
