# API Key Management in Admin Panel

## Overview

API keys for Groq and Mistral can now be configured directly through the admin panel web interface instead of requiring environment variables. This makes it easier to manage and update API keys without needing server access.

## Features

### ✅ Web-Based Configuration
- Configure Groq API Key through admin panel
- Configure Mistral API Key through admin panel
- Secure storage in database
- Fallback to environment variables if database keys not set

### ✅ Admin Panel Integration
- New fields in **API Settings** tab
- Password-masked input fields for security
- Save button updates both keys simultaneously
- Links to API provider websites for obtaining keys

### ✅ Automatic Migration
- Settings table automatically created on first use
- Existing environment variables can be migrated if needed
- No data loss or disruption to existing functionality

## How to Use

### 1. Access Admin Panel
Navigate to `/admin` and log in with admin credentials.

### 2. Go to API Settings Tab
Click on the **🔧 API Settings** tab in the admin panel.

### 3. Enter API Keys
- **Groq API Key**: Enter your Groq API key from [console.groq.com](https://console.groq.com/)
- **Mistral API Key**: Enter your Mistral API key from [console.mistral.ai](https://console.mistral.ai/)

### 4. Save Settings
Click the **Save API Settings** button to store the keys in the database.

### 5. Test Functionality
- Try translating a recipe to verify the API key works
- Try ingredient substitution to test AI integration
- Error messages will guide you if keys are missing or invalid

## Technical Details

### Database Storage
- API keys are stored in the `settings` table
- Key names: `groq_api_key`, `mistral_api_key`
- Values are stored as plain text in database (consider encryption for production)

### Code Changes
1. **New Settings Model** (`models.py:209-238`)
   - Generic key-value storage for application settings
   - Static methods for easy get/set operations
   - Automatic timestamp tracking

2. **Helper Function** (`app.py:75-84`)
   ```python
   def get_api_key(key_name):
       """Get API key from database, fallback to environment variable."""
   ```
   - Checks database first
   - Falls back to environment variable if not in database
   - Used throughout the application

3. **Updated Endpoints**
   - `/api/admin/api-settings` - Save and retrieve API keys
   - All translation endpoints now use database keys
   - Ingredient substitution uses database keys

### Migration Script
Run `migrate_add_settings.py` to create the settings table:
```bash
python migrate_add_settings.py
```

This script:
- Creates the `settings` table
- Optionally migrates existing environment variables
- Safe to run multiple times (uses IF NOT EXISTS)

## Security Considerations

### Current Implementation
- API keys stored as plain text in SQLite database
- Protected by admin authentication
- Not exposed in API responses

### Production Recommendations
1. **Encrypt API Keys**: Use encryption for sensitive data
2. **Use Environment Variables**: For production deployments
3. **Restrict Database Access**: Ensure proper file permissions
4. **Use HTTPS**: Always use HTTPS in production
5. **Audit Logging**: Track when keys are accessed/modified

## Error Messages

The application now provides helpful error messages:

- **"Groq API key not configured. Please set it in the admin panel."**
  - Go to admin panel and add Groq API key

- **"AI service not configured. Please set API keys in the admin panel."**
  - At least one API key (Groq or Mistral) must be configured

- **"No AI service available. Please set API keys in the admin panel."**
  - Both API keys are missing or invalid

## Testing

Run the test script to verify functionality:
```bash
python test_api_keys.py
```

This tests:
- Setting API keys
- Retrieving API keys
- Updating existing keys
- Helper function integration

## Compatibility

### Backward Compatibility
- ✅ Environment variables still work as fallback
- ✅ Existing code unchanged (uses same API key values)
- ✅ No breaking changes to existing deployments

### Environment Variable Fallback
If API keys are not in the database, the system falls back to:
- `GROQ_API_KEY` environment variable
- `MISTRAL_API_KEY` environment variable

## Files Modified

1. `models.py` - Added Settings model
2. `app.py` - Added get_api_key() helper and updated all API key usage
3. `templates/admin.html` - Added API key input fields
4. `static/js/admin.js` - Updated saveApiSettings() to handle API keys
5. `migrate_add_settings.py` - Migration script (new)
6. `test_api_keys.py` - Test script (new)

## Next Steps

You can now:
1. Remove API keys from environment variables (optional)
2. Configure keys through admin panel
3. Update keys anytime without restarting the server
4. Share admin access without sharing server credentials

---

**Note**: This feature is fully tested and ready to use. All translation and ingredient substitution features now work with database-stored API keys.
