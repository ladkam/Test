# NYT Cooking Recipe Translator

A Python application that downloads recipes from New York Times Cooking, converts imperial measurements to metric, and translates them to any language using the Grok API (free tier).

## Features

- 🍳 **Scrapes recipes** from NYT Cooking URLs
- 📏 **Converts measurements** from imperial to metric (cups→ml, oz→g, °F→°C, etc.)
- 🌍 **Translates recipes** to any language using Grok API
- 📝 **Preserves formatting** maintains markdown structure and organization
- 💾 **Saves recipes** as markdown files for easy reading

## Prerequisites

- Python 3.7 or higher
- A Grok API key (free tier available at [x.ai](https://x.ai))

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

4. Edit `.env` and add your Grok API key:
```
GROK_API_KEY=your_actual_api_key_here
TARGET_LANGUAGE=Spanish
```

## Usage

### Basic Usage

Simply provide a NYT Cooking recipe URL:

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

3. **Translation**: The recipe text is sent to the Grok API with specific instructions to translate while preserving formatting and measurements.

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
├── recipe_translator.py    # Main application script
├── recipe_scraper.py        # NYT Cooking scraper
├── unit_converter.py        # Imperial to metric converter
├── grok_translator.py       # Grok API integration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── recipes/                # Output directory (auto-created)
```

## Troubleshooting

### "Error: Please provide a valid NYT Cooking URL"
Make sure you're using a URL from `cooking.nytimes.com`, not regular nytimes.com.

### "Error: Grok API key not provided"
Check that your `.env` file exists and contains a valid `GROK_API_KEY`.

### "Warning: Could not connect to Grok API"
Verify your API key is correct and you have internet connectivity. The script will continue without translation if the API is unavailable.

### Recipe not scraping correctly
Some recipes may have different HTML structures. The scraper tries multiple methods to extract data. If a recipe fails, please open an issue with the URL.

## Limitations

- Only works with NYT Cooking recipes (not general NYT articles)
- Grok API free tier has rate limits
- Some complex measurements may not convert perfectly
- Requires internet connection

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- New York Times Cooking for the amazing recipes
- Grok API by x.ai for translation capabilities
