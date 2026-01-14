# NYT Cooking Recipe Translator

A Python application that downloads recipes from New York Times Cooking, converts imperial measurements to metric, and translates them to any language using Mistral AI (free tier with 1 billion tokens/month).

## Features

### Core Features
- 🌐 **Modern Web Interface** - Responsive web application with authentication
- 🔐 **User Authentication** - Secure login system with role-based access (User & Admin)
- 👤 **Admin Panel** - Manage users, languages, and translation settings
- 🍳 **Recipe Scraping** - Extract recipes from NYT Cooking URLs (with subscriber support)
- 📏 **Unit Conversion** - Automatic imperial to metric conversion (cups→ml, oz→g, °F→°C)
- 🌍 **Multi-language Translation** - Translate to 15+ languages using Mistral AI
- 📝 **Format Preservation** - Maintains markdown structure and formatting
- 🖼️ **Recipe Images** - Automatically extracts and displays recipe photos
- 📋 **Copy to Clipboard** - One-click copy functionality
- 💾 **Download as Markdown** - Save translated recipes locally
- 🖥️ **CLI Support** - Command-line interface for automation

### Admin Features
- **Language Management**: Add or remove translation languages dynamically
- **Prompt Customization**: Edit system and translation prompts for better results
- **User Management**: Create users, assign roles (admin/user), manage access
- **Settings Reset**: Restore default configurations with one click

## Prerequisites

- Python 3.7 or higher
- A Mistral AI API key (free tier with 1 billion tokens/month at [console.mistral.ai](https://console.mistral.ai))

## Default Credentials

After first setup, use these credentials to login:
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the admin password after first login!

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Test
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Mistral AI API key:
```
MISTRAL_API_KEY=your_actual_api_key_here
MISTRAL_MODEL=open-mistral-nemo
SECRET_KEY=your-random-secret-key-for-sessions
TARGET_LANGUAGE=Spanish
```

To get your Mistral API key:
- Go to [console.mistral.ai](https://console.mistral.ai)
- Sign up or log in
- Click "API Keys" in the sidebar
- Create a new API key
- Copy and paste it in your `.env` file

**Security Note**: Change the `SECRET_KEY` to a random string for production use.

## Usage

### Web Application (Recommended)

The easiest way to use the recipe translator is through the web interface:

1. Start the web server:
```bash
python app.py
```

2. Open your browser and go to:
```
http://localhost:5000
```

3. Enter your recipe details:
   - **Recipe URL**: Paste a NYT Cooking recipe URL
   - **Target Language**: Choose from 10+ languages
   - **NYT Cookie** (Optional): For subscriber-only recipes - see instructions below
   - **Options**: Toggle metric conversion and translation

4. Click "Translate Recipe" and view the results in your browser

5. Download the recipe as a markdown file

#### Getting Your NYT Cookie (for Subscriber Recipes)

If you have an NYT Cooking subscription and want to access subscriber-only recipes:

1. Log in to [cooking.nytimes.com](https://cooking.nytimes.com)
2. Open browser Developer Tools (F12 or Right-click → Inspect)
3. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Click on **Cookies** → `https://cooking.nytimes.com`
5. Find the cookie named `NYT-S` and copy its value
6. Paste it in the "NYT Cookie" field in the web app

⚠️ **Security Note**: Your cookie is like a password - keep it private!

### Command Line Interface

You can also use the CLI for automation:

**Basic Usage:**

```bash
python recipe_translator.py https://cooking.nytimes.com/recipes/1234-recipe-name
```

This will:
1. Download the recipe
2. Convert all measurements to metric
3. Translate to the language specified in `.env` (default: Spanish)
4. Save to `recipes/recipe_name.md`

### Advanced Options

**Translate to a specific language:**
```bash
python recipe_translator.py <url> --language French
python recipe_translator.py <url> -l German
```

**Save to a specific file:**
```bash
python recipe_translator.py <url> --output my_recipe.md
python recipe_translator.py <url> -o ~/Desktop/recipe.md
```

**Skip translation (only convert to metric):**
```bash
python recipe_translator.py <url> --no-translate
```

**Skip unit conversion (only translate):**
```bash
python recipe_translator.py <url> --no-convert
```

### Examples

```bash
# Download and translate a cookie recipe to Spanish
python recipe_translator.py https://cooking.nytimes.com/recipes/1019529-chocolate-chip-cookies

# Translate to French and save to a specific location
python recipe_translator.py https://cooking.nytimes.com/recipes/1024016-roasted-salmon --language French --output salmon.md

# Only convert measurements, no translation
python recipe_translator.py https://cooking.nytimes.com/recipes/1014991-banana-bread --no-translate
```

## How It Works

1. **Recipe Scraping**: The application fetches the recipe page and extracts structured data (JSON-LD) or parses the HTML to get the recipe details.

2. **Unit Conversion**: All imperial measurements (cups, tablespoons, ounces, pounds, Fahrenheit) are automatically converted to metric equivalents (ml, liters, grams, kg, Celsius). The original measurements are kept in parentheses for reference.

3. **Translation**: The recipe text is sent to Mistral AI with specific instructions to translate while preserving formatting and measurements.

4. **Output**: The final recipe is saved as a markdown file with all formatting preserved.

## Supported Conversions

### Volume
- Cups → Milliliters (ml) or Liters (l)
- Tablespoons/Teaspoons → Milliliters (ml)
- Fluid ounces → Milliliters (ml)
- Pints/Quarts/Gallons → Liters (l)

### Weight
- Ounces → Grams (g)
- Pounds → Grams (g) or Kilograms (kg)

### Temperature
- Fahrenheit (°F) → Celsius (°C)

## Project Structure

```
.
├── app.py                   # Flask web application
├── recipe_translator.py     # CLI application
├── recipe_scraper.py        # NYT Cooking scraper (with auth support)
├── unit_converter.py        # Imperial to metric converter
├── mistral_translator.py    # Mistral AI API integration
├── grok_translator.py       # Legacy (kept for compatibility)
├── templates/
│   └── index.html          # Web UI template
├── static/
│   ├── css/
│   │   └── style.css       # Web UI styles
│   └── js/
│       └── app.js          # Web UI JavaScript
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── recipes/                # Output directory (auto-created)
```

## Troubleshooting

### "Error: Please provide a valid NYT Cooking URL"
Make sure you're using a URL from `cooking.nytimes.com`, not regular nytimes.com.

### "Error: Mistral API key not provided"
Check that your `.env` file exists and contains a valid `MISTRAL_API_KEY`.

### "Warning: Could not connect to Mistral API"
Verify your API key is correct and you have internet connectivity. The script will continue without translation if the API is unavailable. You can test your connection with:
```bash
python test_mistral_api.py
```

### Recipe not scraping correctly
Some recipes may have different HTML structures. The scraper tries multiple methods to extract data. If a recipe fails, please open an issue with the URL.

## Limitations

- Only works with NYT Cooking recipes (not general NYT articles)
- Free recipes work without authentication; subscriber-only recipes require your NYT cookie
- Mistral AI free tier: 1 billion tokens/month (very generous!)
- Some complex measurements may not convert perfectly
- Requires internet connection
- NYT cookies expire periodically and need to be updated

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Authentication**: Flask-Login with role-based access control
- **Translation**: Mistral AI API (1 billion free tokens/month)
- **Frontend**: Vanilla JavaScript, responsive CSS
- **Storage**: JSON-based (users, settings)
- **Web Scraping**: BeautifulSoup4 + lxml

## Why Mistral AI?

- ✅ **Generous Free Tier**: 1 billion tokens/month (no credit card required)
- ✅ **High Quality**: Excellent translation quality
- ✅ **Fast**: Quick response times
- ✅ **European AI**: Privacy-focused, GDPR compliant
- ✅ **Configurable**: Customize prompts via admin panel
- ✅ **Multiple Models**: Choose from various models (open-mistral-nemo recommended for free tier)

## Security Features

- 🔒 Password hashing with Werkzeug
- 🔐 Session-based authentication
- 👤 Role-based access control (User & Admin)
- 🛡️ Protected admin routes
- 🔑 Secure cookie handling
- ⚠️ CSRF protection via Flask

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- New York Times Cooking for the amazing recipes
- Mistral AI for providing excellent free-tier translation capabilities
