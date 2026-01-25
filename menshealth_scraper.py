"""
Recipe scraper for Men's Health website.
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


class MensHealthRecipeScraper:
    """Scraper for Men's Health recipes."""

    def __init__(self):
        """Initialize the scraper."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape_recipe(self, url: str) -> Dict:
        """
        Scrape a recipe from Men's Health.

        Args:
            url: The Men's Health recipe URL

        Returns:
            Dictionary containing recipe information
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch recipe: {str(e)}")

        soup = BeautifulSoup(response.content, 'lxml')

        # Try to extract JSON-LD structured data first (most reliable)
        recipe_data = self._extract_json_ld(soup)

        if not recipe_data:
            # Fallback to HTML parsing
            recipe_data = self._extract_from_html(soup)

        # Add source URL
        recipe_data['url'] = url

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
            'url': '',
            'image': '',
            'nutrition': {}
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
            for instruction in instructions:
                if isinstance(instruction, dict):
                    # HowToStep format
                    text = instruction.get('text', '') or instruction.get('itemListElement', {}).get('text', '')
                elif isinstance(instruction, str):
                    text = instruction
                else:
                    continue

                if text:
                    recipe['instructions'].append(text)
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

        # Extract nutrition information
        nutrition_data = data.get('nutrition', {})
        if isinstance(nutrition_data, dict):
            recipe['nutrition'] = {
                'calories': nutrition_data.get('calories', ''),
                'protein': nutrition_data.get('proteinContent', ''),
                'fat': nutrition_data.get('fatContent', ''),
                'saturated_fat': nutrition_data.get('saturatedFatContent', ''),
                'carbohydrates': nutrition_data.get('carbohydrateContent', ''),
                'fiber': nutrition_data.get('fiberContent', ''),
                'sugar': nutrition_data.get('sugarContent', ''),
                'sodium': nutrition_data.get('sodiumContent', ''),
                'cholesterol': nutrition_data.get('cholesterolContent', '')
            }
            # Remove empty values
            recipe['nutrition'] = {k: v for k, v in recipe['nutrition'].items() if v}

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
            'image': '',
            'nutrition': {}
        }

        # Extract title
        title_tag = soup.find('h1', class_=re.compile('recipe.*title', re.I))
        if not title_tag:
            title_tag = soup.find('h1')
        recipe['title'] = title_tag.get_text(strip=True) if title_tag else ''

        # Extract description
        desc_tag = soup.find('meta', {'name': 'description'})
        if not desc_tag:
            desc_tag = soup.find('meta', {'property': 'og:description'})
        if desc_tag:
            recipe['description'] = desc_tag.get('content', '')

        # Extract image
        image_tag = soup.find('meta', property='og:image')
        if not image_tag:
            image_tag = soup.find('img', class_=re.compile('recipe.*image', re.I))
        if image_tag:
            recipe['image'] = image_tag.get('content') or image_tag.get('src', '')

        # Extract yield/servings
        yield_tag = soup.find(class_=re.compile('yield|servings', re.I))
        if not yield_tag:
            yield_tag = soup.find('span', {'itemprop': 'recipeYield'})
        recipe['yield'] = yield_tag.get_text(strip=True) if yield_tag else ''

        # Extract ingredients - try multiple patterns
        ingredient_tags = soup.find_all('li', class_=re.compile('ingredient', re.I))
        if not ingredient_tags:
            ingredient_tags = soup.find_all('span', {'itemprop': 'recipeIngredient'})
        if not ingredient_tags:
            # Try finding ingredient lists
            ing_list = soup.find('ul', class_=re.compile('ingredient', re.I))
            if ing_list:
                ingredient_tags = ing_list.find_all('li')

        for tag in ingredient_tags:
            ingredient = tag.get_text(strip=True)
            if ingredient:
                recipe['ingredients'].append(ingredient)

        # Extract instructions - try multiple patterns
        instruction_tags = soup.find_all('li', class_=re.compile('instruction|step', re.I))
        if not instruction_tags:
            instruction_tags = soup.find_all('span', {'itemprop': 'recipeInstructions'})
        if not instruction_tags:
            # Try finding instruction lists
            inst_list = soup.find('ol', class_=re.compile('instruction|step|preparation', re.I))
            if inst_list:
                instruction_tags = inst_list.find_all('li')

        for tag in instruction_tags:
            instruction = tag.get_text(strip=True)
            if instruction:
                recipe['instructions'].append(instruction)

        # Extract author
        author_tag = soup.find('a', class_=re.compile('author', re.I))
        if not author_tag:
            author_tag = soup.find('span', {'itemprop': 'author'})
        if not author_tag:
            author_tag = soup.find('meta', {'name': 'author'})
            if author_tag:
                recipe['author'] = author_tag.get('content', '')
        if author_tag and not recipe['author']:
            recipe['author'] = author_tag.get_text(strip=True)

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

        # Nutrition information
        nutrition = recipe.get('nutrition', {})
        if nutrition:
            output.append("## Nutrition (per serving)\n")
            nutrition_labels = {
                'calories': 'Calories',
                'protein': 'Protein',
                'fat': 'Total Fat',
                'saturated_fat': 'Saturated Fat',
                'carbohydrates': 'Carbohydrates',
                'fiber': 'Fiber',
                'sugar': 'Sugar',
                'sodium': 'Sodium',
                'cholesterol': 'Cholesterol'
            }
            for key, label in nutrition_labels.items():
                if key in nutrition and nutrition[key]:
                    output.append(f"- **{label}:** {nutrition[key]}")
            output.append("")

        # Ingredients
        output.append("## Ingredients\n")
        for ingredient in recipe['ingredients']:
            output.append(f"- {ingredient}")
        output.append("")

        # Instructions
        output.append("## Instructions\n")
        for idx, instruction in enumerate(recipe['instructions'], 1):
            output.append(f"{idx}. {instruction}")
        output.append("")

        return "\n".join(output)
