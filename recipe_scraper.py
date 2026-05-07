"""
Generic recipe scraper.

Parses any URL that publishes schema.org/Recipe data via JSON-LD
(BBC Good Food, Marmiton, Chefkoch, NYT Cooking, AllRecipes, Serious Eats,
and most modern recipe sites). Falls back to a microdata/HTML scrape when
JSON-LD is missing.

All ingredient and instruction strings are converted to metric before
returning, since this app is metric-only.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from unit_converter import convert_to_metric


BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class RecipeScrapeError(Exception):
    """Raised when a URL can't be fetched or no recipe is found."""


def parse_iso_duration(duration: str) -> str:
    """Convert ISO 8601 duration (PT1H30M) to a human-readable string."""
    if not duration or not isinstance(duration, str) or not duration.startswith("PT"):
        return duration or ""

    body = duration[2:]
    hours = int(m.group(1)) if (m := re.search(r"(\d+)H", body)) else 0
    minutes = int(m.group(1)) if (m := re.search(r"(\d+)M", body)) else 0

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    return " ".join(parts) if parts else duration


def _matches_recipe(at_type: Any) -> bool:
    if at_type == "Recipe":
        return True
    if isinstance(at_type, list) and "Recipe" in at_type:
        return True
    return False


def _walk_for_recipe(node: Any) -> Optional[Dict]:
    """Recursively descend dicts/lists looking for a Recipe object."""
    if isinstance(node, dict):
        if _matches_recipe(node.get("@type")):
            return node
        for key in ("@graph", "mainEntity", "mainEntityOfPage", "itemListElement"):
            if key in node:
                found = _walk_for_recipe(node[key])
                if found:
                    return found
        for value in node.values():
            if isinstance(value, (dict, list)):
                found = _walk_for_recipe(value)
                if found:
                    return found
    elif isinstance(node, list):
        for item in node:
            found = _walk_for_recipe(item)
            if found:
                return found
    return None


def _extract_json_ld(soup: BeautifulSoup) -> Optional[Dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                data = json.loads(raw.replace("\n", " "))
            except json.JSONDecodeError:
                continue
        recipe = _walk_for_recipe(data)
        if recipe:
            return recipe
    return None


def _first_image(image_field: Any) -> str:
    if isinstance(image_field, str):
        return image_field
    if isinstance(image_field, dict):
        return image_field.get("url", "") or ""
    if isinstance(image_field, list) and image_field:
        first = image_field[0]
        if isinstance(first, dict):
            return first.get("url", "") or ""
        return str(first)
    return ""


def _author_name(author_field: Any) -> str:
    if isinstance(author_field, dict):
        return author_field.get("name", "") or ""
    if isinstance(author_field, list) and author_field:
        first = author_field[0]
        if isinstance(first, dict):
            return first.get("name", "") or ""
        return str(first)
    return str(author_field) if author_field else ""


def _flatten_instructions(field: Any) -> List[str]:
    out: List[str] = []
    if isinstance(field, str):
        return [field]
    if isinstance(field, list):
        for item in field:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if t == "HowToSection":
                    out.extend(_flatten_instructions(item.get("itemListElement", [])))
                else:
                    text = item.get("text") or item.get("name") or ""
                    if text:
                        out.append(text)
            elif isinstance(item, str):
                out.append(item)
    return out


def _parse_json_ld_recipe(data: Dict) -> Dict:
    ingredients = data.get("recipeIngredient") or data.get("ingredients") or []
    if isinstance(ingredients, str):
        ingredients = [ingredients]

    instructions = _flatten_instructions(data.get("recipeInstructions") or [])

    nutrition_data = data.get("nutrition") or {}
    nutrition: Dict[str, str] = {}
    if isinstance(nutrition_data, dict):
        for key, label in (
            ("calories", "calories"),
            ("proteinContent", "protein"),
            ("fatContent", "fat"),
            ("saturatedFatContent", "saturated_fat"),
            ("carbohydrateContent", "carbohydrates"),
            ("fiberContent", "fiber"),
            ("sugarContent", "sugar"),
            ("sodiumContent", "sodium"),
            ("cholesterolContent", "cholesterol"),
        ):
            value = nutrition_data.get(key)
            if value:
                nutrition[label] = value

    return {
        "title": data.get("name", "") or "",
        "description": data.get("description", "") or "",
        "yield": data.get("recipeYield", "") or "",
        "time": {
            "prep": parse_iso_duration(data.get("prepTime", "") or ""),
            "cook": parse_iso_duration(data.get("cookTime", "") or ""),
            "total": parse_iso_duration(data.get("totalTime", "") or ""),
        },
        "ingredients": [str(i) for i in ingredients],
        "instructions": [str(i) for i in instructions],
        "author": _author_name(data.get("author", "")),
        "url": data.get("url", "") or "",
        "image": _first_image(data.get("image", "")),
        "nutrition": nutrition,
    }


def _extract_from_html(soup: BeautifulSoup) -> Dict:
    """Best-effort microdata/HTML scrape when no JSON-LD recipe is present."""
    title_tag = soup.find(attrs={"itemprop": "name"}) or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    description = ""
    desc_tag = soup.find("meta", {"name": "description"}) or soup.find(
        "meta", {"property": "og:description"}
    )
    if desc_tag:
        description = desc_tag.get("content", "") or ""

    image = ""
    og_image = soup.find("meta", {"property": "og:image"})
    if og_image:
        image = og_image.get("content", "") or ""

    ingredient_tags = soup.find_all(attrs={"itemprop": "recipeIngredient"})
    if not ingredient_tags:
        ingredient_tags = soup.find_all("li", class_=re.compile("ingredient", re.I))
    ingredients = [tag.get_text(strip=True) for tag in ingredient_tags if tag.get_text(strip=True)]

    instruction_tags = soup.find_all(attrs={"itemprop": "recipeInstructions"})
    if not instruction_tags:
        instruction_tags = soup.find_all("li", class_=re.compile("instruction|preparation|step", re.I))
    instructions = [tag.get_text(strip=True) for tag in instruction_tags if tag.get_text(strip=True)]

    return {
        "title": title,
        "description": description,
        "yield": "",
        "time": {"prep": "", "cook": "", "total": ""},
        "ingredients": ingredients,
        "instructions": instructions,
        "author": "",
        "url": "",
        "image": image,
        "nutrition": {},
    }


def _convert_recipe_to_metric(recipe: Dict) -> Dict:
    recipe["ingredients"] = [convert_to_metric(i) for i in recipe.get("ingredients", [])]
    recipe["instructions"] = [convert_to_metric(s) for s in recipe.get("instructions", [])]
    return recipe


def scrape_recipe(url: str, *, timeout: int = 30) -> Dict:
    """Fetch and parse a recipe at `url`, returning a metric-converted dict.

    Raises RecipeScrapeError if the URL can't be fetched or no recipe is found.
    """
    try:
        response = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RecipeScrapeError(f"Failed to fetch recipe: {e}") from e

    soup = BeautifulSoup(response.content, "lxml")
    recipe_data = _extract_json_ld(soup)
    if not recipe_data:
        recipe_data = None

    recipe = _parse_json_ld_recipe(recipe_data) if recipe_data else _extract_from_html(soup)

    if not recipe.get("title") and not recipe.get("ingredients"):
        raise RecipeScrapeError("No recipe data found on page")

    recipe["source_host"] = urlparse(url).netloc
    if not recipe.get("url"):
        recipe["url"] = url

    return _convert_recipe_to_metric(recipe)


def format_recipe(recipe: Dict) -> str:
    """Render a recipe dict as readable markdown."""
    out: List[str] = [f"# {recipe.get('title', '')}\n"]
    if recipe.get("author"):
        out.append(f"**By:** {recipe['author']}\n")
    if recipe.get("description"):
        out.append(f"{recipe['description']}\n")
    if recipe.get("yield"):
        out.append(f"**Yield:** {recipe['yield']}\n")

    time_info = recipe.get("time", {}) or {}
    parts = []
    if time_info.get("prep"):
        parts.append(f"Prep: {time_info['prep']}")
    if time_info.get("cook"):
        parts.append(f"Cook: {time_info['cook']}")
    if time_info.get("total"):
        parts.append(f"Total: {time_info['total']}")
    if parts:
        out.append(f"**Time:** {', '.join(parts)}\n")

    nutrition = recipe.get("nutrition") or {}
    if nutrition:
        out.append("## Nutrition (per serving)\n")
        labels = {
            "calories": "Calories",
            "protein": "Protein",
            "fat": "Total Fat",
            "saturated_fat": "Saturated Fat",
            "carbohydrates": "Carbohydrates",
            "fiber": "Fiber",
            "sugar": "Sugar",
            "sodium": "Sodium",
            "cholesterol": "Cholesterol",
        }
        for key, label in labels.items():
            if nutrition.get(key):
                out.append(f"- **{label}:** {nutrition[key]}")
        out.append("")

    out.append("## Ingredients\n")
    for ing in recipe.get("ingredients", []):
        out.append(f"- {ing}")
    out.append("")

    out.append("## Instructions\n")
    for idx, step in enumerate(recipe.get("instructions", []), 1):
        out.append(f"{idx}. {step}")
    out.append("")

    return "\n".join(out)
