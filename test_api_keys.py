#!/usr/bin/env python3
"""
Test script for API key management in admin panel.
"""
from app import app, db
from models import Settings as SettingsModel

def test_api_keys():
    """Test API key storage and retrieval."""
    with app.app_context():
        print("Testing API key management...\n")

        # Test 1: Set API keys
        print("1. Setting test API keys...")
        SettingsModel.set('groq_api_key', 'test_groq_key_12345')
        SettingsModel.set('mistral_api_key', 'test_mistral_key_67890')
        print("   ✅ API keys set successfully")

        # Test 2: Retrieve API keys
        print("\n2. Retrieving API keys...")
        groq_key = SettingsModel.get('groq_api_key')
        mistral_key = SettingsModel.get('mistral_api_key')
        print(f"   Groq API Key: {groq_key}")
        print(f"   Mistral API Key: {mistral_key}")

        # Test 3: Verify values
        print("\n3. Verifying values...")
        assert groq_key == 'test_groq_key_12345', "Groq key mismatch!"
        assert mistral_key == 'test_mistral_key_67890', "Mistral key mismatch!"
        print("   ✅ Values verified successfully")

        # Test 4: Update existing keys
        print("\n4. Updating existing keys...")
        SettingsModel.set('groq_api_key', 'updated_groq_key_abcde')
        updated_key = SettingsModel.get('groq_api_key')
        print(f"   Updated Groq API Key: {updated_key}")
        assert updated_key == 'updated_groq_key_abcde', "Update failed!"
        print("   ✅ Update successful")

        # Test 5: Test get_api_key helper function
        print("\n5. Testing get_api_key helper function...")
        from app import get_api_key
        groq_from_helper = get_api_key('groq_api_key')
        print(f"   Groq key from helper: {groq_from_helper}")
        assert groq_from_helper == 'updated_groq_key_abcde', "Helper function failed!"
        print("   ✅ Helper function works correctly")

        # Clean up test data
        print("\n6. Cleaning up test data...")
        SettingsModel.set('groq_api_key', '')
        SettingsModel.set('mistral_api_key', '')
        print("   ✅ Test data cleaned up")

        print("\n" + "="*50)
        print("✅ All API key management tests passed!")
        print("="*50)

if __name__ == '__main__':
    test_api_keys()
