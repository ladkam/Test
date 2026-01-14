"""
Recipe scraper for New York Times Cooking website.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional


def parse_iso_duration(duration: str) -> str:
    """
    Convert ISO 8601 duration format to human-readable time.
    Examples: PT5M -> 5 minutes, PT1H30M -> 1 hour 30 minutes
    """
    if not duration or not duration.startswith('PT'):
        return duration

    duration = duration[2:]  # Remove 'PT'
    hours = 0
    minutes = 0

    # Extract hours
    hour_match = re.search(r'(\d+)H', duration)
    if hour_match:
        hours = int(hour_match.group(1))

    # Extract minutes
    min_match = re.search(r'(\d+)M', duration)
    if min_match:
        minutes = int(min_match.group(1))

    # Build human-readable string
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

    return ' '.join(parts) if parts else duration


class NYTRecipeScraper:
    """Scraper for New York Times Cooking recipes."""

    def __init__(self, nyt_cookie: Optional[str] = None):
        """
        Initialize the scraper.

        Args:
            nyt_cookie: Optional NYT-S cookie for authenticated access
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.cookies = {}
        if nyt_cookie:
            self.cookies['NYT-S'] = nyt_cookie

    def scrape_recipe(self, url: str) -> Dict:
        """
        Scrape a recipe from NYT Cooking.

        Args:
            url: The NYT Cooking recipe URL

        Returns:
            Dictionary containing recipe information
        """
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch recipe: {str(e)}")

        soup = BeautifulSoup(response.content, 'lxml')

        # Try to extract JSON-LD structured data first (most reliable)
        recipe_data = self._extract_json_ld(soup)

        if not recipe_data:
            # Fallback to HTML parsing
            recipe_data = self._extract_from_html(soup)

        return recipe_data

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract recipe data from JSON-LD structured data."""
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                data = json.loads(script.string)

                # Handle both single object and array
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Recipe':
                            return self._parse_json_ld_recipe(item)
                elif isinstance(data, dict) and data.get('@type') == 'Recipe':
                    return self._parse_json_ld_recipe(data)
            except (json.JSONDecodeError, AttributeError):
                continue

        return None

    def _parse_json_ld_recipe(self, data: Dict) -> Dict:
        """Parse JSON-LD recipe data into our format."""
        recipe = {
            'title': data.get('name', ''),
            'description': data.get('description', ''),
            'yield': data.get('recipeYield', ''),
            'time': {
                'prep': parse_iso_duration(data.get('prepTime', '')),
                'cook': parse_iso_duration(data.get('cookTime', '')),
                'total': parse_iso_duration(data.get('totalTime', ''))
            },
            'ingredients': [],
            'instructions': [],
            'author': '',
            'url': data.get('url', ''),
            'image': ''
        }

        # Extract image
        image = data.get('image', '')
        if isinstance(image, dict):
            recipe['image'] = image.get('url', '')
        elif isinstance(image, list) and len(image) > 0:
            if isinstance(image[0], dict):
                recipe['image'] = image[0].get('url', '')
            else:
                recipe['image'] = image[0]
        elif isinstance(image, str):
            recipe['image'] = image

        # Extract ingredients
        ingredients = data.get('recipeIngredient', [])
        if isinstance(ingredients, list):
            recipe['ingredients'] = ingredients
        elif isinstance(ingredients, str):
            recipe['ingredients'] = [ingredients]

        # Extract instructions
        instructions = data.get('recipeInstructions', [])
        if isinstance(instructions, list):
            for idx, instruction in enumerate(instructions, 1):
                if isinstance(instruction, dict):
                    text = instruction.get('text', '')
                elif isinstance(instruction, str):
                    text = instruction
                else:
                    continue

                if text:
                    recipe['instructions'].append(f"{idx}. {text}")
        elif isinstance(instructions, str):
            recipe['instructions'] = [instructions]

        # Extract author
        author = data.get('author', {})
        if isinstance(author, dict):
            recipe['author'] = author.get('name', '')
        elif isinstance(author, list) and len(author) > 0:
            recipe['author'] = author[0].get('name', '') if isinstance(author[0], dict) else str(author[0])
        else:
            recipe['author'] = str(author) if author else ''

        return recipe

    def _extract_from_html(self, soup: BeautifulSoup) -> Dict:
        """Fallback method to extract recipe data from HTML."""
        recipe = {
            'title': '',
            'description': '',
            'yield': '',
            'time': {'prep': '', 'cook': '', 'total': ''},
            'ingredients': [],
            'instructions': [],
            'author': '',
            'url': '',
            'image': ''
        }

        # Extract image
        image_tag = soup.find('img', class_=re.compile('recipe.*image', re.I))
        if not image_tag:
            image_tag = soup.find('meta', property='og:image')
        if image_tag:
            recipe['image'] = image_tag.get('content') or image_tag.get('src', '')

        # Extract title
        title_tag = soup.find('h1', class_=re.compile('recipe.*title|pantry.*title', re.I))
        if not title_tag:
            title_tag = soup.find('h1')
        recipe['title'] = title_tag.get_text(strip=True) if title_tag else ''

        # Extract description
        desc_tag = soup.find('meta', {'name': 'description'})
        if desc_tag:
            recipe['description'] = desc_tag.get('content', '')

        # Extract yield/servings
        yield_tag = soup.find(class_=re.compile('yield|servings', re.I))
        recipe['yield'] = yield_tag.get_text(strip=True) if yield_tag else ''

        # Extract ingredients
        ingredient_tags = soup.find_all('li', class_=re.compile('ingredient', re.I))
        if not ingredient_tags:
            ingredient_tags = soup.find_all('span', {'itemprop': 'recipeIngredient'})

        for tag in ingredient_tags:
            ingredient = tag.get_text(strip=True)
            if ingredient:
                recipe['ingredients'].append(ingredient)

        # Extract instructions
        instruction_tags = soup.find_all('li', class_=re.compile('instruction|preparation', re.I))
        if not instruction_tags:
            instruction_tags = soup.find_all('ol', class_=re.compile('recipe|preparation', re.I))
            if instruction_tags:
                instruction_tags = instruction_tags[0].find_all('li')

        for idx, tag in enumerate(instruction_tags, 1):
            instruction = tag.get_text(strip=True)
            if instruction:
                recipe['instructions'].append(f"{idx}. {instruction}")

        # Extract author
        author_tag = soup.find(class_=re.compile('author', re.I))
        if not author_tag:
            author_tag = soup.find('span', {'itemprop': 'author'})
        recipe['author'] = author_tag.get_text(strip=True) if author_tag else ''

        return recipe

    def format_recipe(self, recipe: Dict) -> str:
        """Format recipe data as readable text."""
        output = []

        output.append(f"# {recipe['title']}\n")

        if recipe['author']:
            output.append(f"**By:** {recipe['author']}\n")

        if recipe['description']:
            output.append(f"{recipe['description']}\n")

        if recipe['yield']:
            output.append(f"**Yield:** {recipe['yield']}\n")

        # Time information
        time_info = []
        if recipe['time']['prep']:
            time_info.append(f"Prep: {recipe['time']['prep']}")
        if recipe['time']['cook']:
            time_info.append(f"Cook: {recipe['time']['cook']}")
        if recipe['time']['total']:
            time_info.append(f"Total: {recipe['time']['total']}")

        if time_info:
            output.append(f"**Time:** {', '.join(time_info)}\n")

        # Ingredients
        output.append("## Ingredients\n")
        for ingredient in recipe['ingredients']:
            output.append(f"- {ingredient}")
        output.append("")

        # Instructions
        output.append("## Instructions\n")
        for instruction in recipe['instructions']:
            output.append(instruction)
            output.append("")

        return "\n".join(output)
