/**
 * Weekly Planner functionality
 */

let currentPlan = [];
let allRecipes = [];

// Unit system preference (default to metric)
window.unitSystem = localStorage.getItem('unitSystem') || 'metric';

// Unit conversion functions
function convertToMetric(text) {
    let converted = text;

    // Temperature: Fahrenheit to Celsius
    converted = converted.replace(/(\d+)\s*°?\s*F\b/gi, (match, temp) => {
        const celsius = Math.round((parseFloat(temp) - 32) * 5 / 9);
        return `${celsius}°C`;
    });

    // Cups to ml
    converted = converted.replace(/(\d+\.?\d*)\s*cups?\b/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 240);
        return `${ml}ml`;
    });

    // Tablespoons to ml
    converted = converted.replace(/(\d+\.?\d*)\s*(tbsp|tablespoons?)\b/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 15);
        return `${ml}ml`;
    });

    // Teaspoons to ml
    converted = converted.replace(/(\d+\.?\d*)\s*(tsp|teaspoons?)\b/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 5);
        return `${ml}ml`;
    });

    // Fluid ounces to ml
    converted = converted.replace(/(\d+\.?\d*)\s*(fl\.?\s*oz|fluid\s*ounces?)\b/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 30);
        return `${ml}ml`;
    });

    // Ounces (weight) to grams
    converted = converted.replace(/(\d+\.?\d*)\s*oz\b/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 28);
        return `${g}g`;
    });

    // Pounds to grams/kg
    converted = converted.replace(/(\d+\.?\d*)\s*(lbs?|pounds?)\b/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 454);
        if (g >= 1000) {
            return `${(g / 1000).toFixed(1)}kg`;
        }
        return `${g}g`;
    });

    // Inches to cm
    converted = converted.replace(/(\d+\.?\d*)\s*(inches?|in\.?)\b/gi, (match, amount) => {
        const cm = Math.round(parseFloat(amount) * 2.54 * 10) / 10;
        return `${cm}cm`;
    });

    // Quarts to liters
    converted = converted.replace(/(\d+\.?\d*)\s*(quarts?|qt\.?)\b/gi, (match, amount) => {
        const l = Math.round(parseFloat(amount) * 0.946 * 10) / 10;
        return `${l}L`;
    });

    // Pints to ml
    converted = converted.replace(/(\d+\.?\d*)\s*(pints?|pt\.?)\b/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 473);
        return `${ml}ml`;
    });

    // Gallons to liters
    converted = converted.replace(/(\d+\.?\d*)\s*(gallons?|gal\.?)\b/gi, (match, amount) => {
        const l = Math.round(parseFloat(amount) * 3.785 * 10) / 10;
        return `${l}L`;
    });

    return converted;
}

function convertToImperial(text) {
    let converted = text;

    // Temperature: Celsius to Fahrenheit
    converted = converted.replace(/(\d+)\s*°?\s*C\b/gi, (match, temp) => {
        const fahrenheit = Math.round(parseFloat(temp) * 9 / 5 + 32);
        return `${fahrenheit}°F`;
    });

    // ml to cups/tbsp/tsp (choose appropriate unit)
    converted = converted.replace(/(\d+\.?\d*)\s*ml\b/gi, (match, amount) => {
        const ml = parseFloat(amount);
        if (ml >= 240) {
            const cups = Math.round(ml / 240 * 10) / 10;
            return `${cups} cup${cups !== 1 ? 's' : ''}`;
        } else if (ml >= 15) {
            const tbsp = Math.round(ml / 15 * 10) / 10;
            return `${tbsp} tbsp`;
        } else {
            const tsp = Math.round(ml / 5 * 10) / 10;
            return `${tsp} tsp`;
        }
    });

    // Liters to quarts
    converted = converted.replace(/(\d+\.?\d*)\s*L\b/g, (match, amount) => {
        const quarts = Math.round(parseFloat(amount) * 1.057 * 10) / 10;
        return `${quarts} qt`;
    });

    // kg to pounds
    converted = converted.replace(/(\d+\.?\d*)\s*kg\b/gi, (match, amount) => {
        const lbs = Math.round(parseFloat(amount) * 2.205 * 10) / 10;
        return `${lbs} lbs`;
    });

    // grams to ounces
    converted = converted.replace(/(\d+\.?\d*)\s*g\b/gi, (match, amount) => {
        const oz = Math.round(parseFloat(amount) / 28 * 10) / 10;
        return `${oz} oz`;
    });

    // cm to inches
    converted = converted.replace(/(\d+\.?\d*)\s*cm\b/gi, (match, amount) => {
        const inches = Math.round(parseFloat(amount) / 2.54 * 10) / 10;
        return `${inches} in`;
    });

    return converted;
}

function convertUnits(text) {
    if (window.unitSystem === 'metric') {
        return convertToMetric(text);
    } else {
        return convertToImperial(text);
    }
}

function toggleUnitSystem() {
    window.unitSystem = window.unitSystem === 'metric' ? 'imperial' : 'metric';
    localStorage.setItem('unitSystem', window.unitSystem);

    // Update toggle button text
    updateUnitToggleButton();

    // Refresh ingredients and instructions
    if (window.currentRecipeData) {
        const ingredientsSection = document.getElementById('ingredientsSection');
        if (ingredientsSection) {
            ingredientsSection.innerHTML = buildIngredientsListHtml(window.currentRecipeData, window.currentServings);
        }

        const instructionsSection = document.getElementById('instructionsSection');
        if (instructionsSection) {
            instructionsSection.innerHTML = buildInstructionsHtml(window.currentRecipeData);
        }
    }
}

function updateUnitToggleButton() {
    const btn = document.getElementById('unitToggleBtn');
    if (btn) {
        btn.textContent = window.unitSystem === 'metric' ? '📏 Metric' : '📐 Imperial';
        btn.title = `Switch to ${window.unitSystem === 'metric' ? 'Imperial' : 'Metric'}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadCurrentPlan();
    loadAvailableRecipes();

    // Event listeners
    document.getElementById('searchRecipes').addEventListener('input', filterAvailableRecipes);
    document.getElementById('generateShoppingList').addEventListener('click', generateShoppingList);
    document.getElementById('clearPlan').addEventListener('click', clearPlan);

    // Allow Enter key to confirm servings in the modal
    document.getElementById('servingsInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirmServings();
        }
    });
});

async function loadCurrentPlan() {
    try {
        const response = await fetch('/api/planner/current');
        const data = await response.json();

        if (data.success) {
            currentPlan = data.recipes || [];
            displayCurrentPlan();
        }
    } catch (error) {
        console.error('Error loading plan:', error);
    }
}

async function loadAvailableRecipes() {
    try {
        const response = await fetch('/api/recipes');
        const data = await response.json();

        if (data.success) {
            allRecipes = data.recipes;
            displayAvailableRecipes();
        }
    } catch (error) {
        console.error('Error loading recipes:', error);
    }
}

function displayCurrentPlan() {
    const planList = document.getElementById('planList');
    const countEl = document.getElementById('recipeCount');

    countEl.textContent = `${currentPlan.length} ${currentPlan.length === 1 ? 'recipe' : 'recipes'}`;

    if (currentPlan.length === 0) {
        planList.innerHTML = `
            <div class="empty-plan">
                <p>No recipes in your plan yet</p>
                <a href="/library" class="btn btn-primary">Browse Library</a>
            </div>
        `;
        return;
    }

    planList.innerHTML = currentPlan.map(recipe => {
        const healthScoreBadge = getHealthScoreBadge(recipe.health_score);

        return `
        <div class="plan-item" onclick="showRecipeDetail(${recipe.id})" style="cursor: pointer;">
            <button onclick="event.stopPropagation(); removeFromPlan(${recipe.id})" class="btn-remove-overlay" title="Remove from plan">
                <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                    <path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            </button>

            ${recipe.image_url
                ? `<div class="plan-item-image-wrapper">
                     <img src="${recipe.image_url}" class="plan-item-image" alt="${recipe.title}">
                   </div>`
                : '<div class="plan-item-image-placeholder">🍽️</div>'}

            <div class="plan-item-content">
                <h3 class="plan-item-title">${escapeHtml(recipe.title)}</h3>

                <div class="plan-item-meta">
                    ${recipe.total_time ? `
                        <span class="meta-badge">
                            <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                                <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M10 6v4l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            ${formatTime(recipe.total_time)}
                        </span>
                    ` : ''}
                    ${recipe.servings ? `
                        <span class="meta-badge">
                            <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                                <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M7 13h6M10 7v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            ${escapeHtml(recipe.servings)}
                        </span>
                    ` : ''}
                </div>

                ${healthScoreBadge}
            </div>
        </div>
        `;
    }).join('');
}

function filterAvailableRecipes() {
    displayAvailableRecipes();
}

function displayAvailableRecipes() {
    const searchTerm = document.getElementById('searchRecipes').value.toLowerCase();
    const planRecipeIds = new Set(currentPlan.map(r => r.id));

    const filtered = allRecipes.filter(recipe => {
        if (planRecipeIds.has(recipe.id)) return false;
        if (!searchTerm) return true;

        return recipe.title?.toLowerCase().includes(searchTerm);
    });

    const grid = document.getElementById('availableRecipes');

    if (filtered.length === 0) {
        grid.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">No recipes available</p>';
        return;
    }

    grid.innerHTML = filtered.map(recipe => {
        const healthScoreHtml = getHealthScoreBadge(recipe.health_score);
        return `
            <div class="available-recipe-card">
                ${recipe.image_url ? `<img src="${recipe.image_url}" class="available-recipe-image" alt="${recipe.title}">` : '<div class="available-recipe-placeholder">No Image</div>'}
                <div class="available-recipe-content">
                    <h4>${escapeHtml(recipe.title)}</h4>
                    ${recipe.total_time ? `<span class="recipe-time">⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                    ${healthScoreHtml}
                </div>
                <button onclick="addToPlan(${recipe.id})" class="btn btn-primary btn-sm">Add to Plan</button>
            </div>
        `;
    }).join('');
}

function getHealthScoreBadge(healthScore) {
    if (!healthScore || !healthScore.grade || !healthScore.score) {
        return '';
    }

    const gradeClass = `grade-${healthScore.grade.toLowerCase()}`;
    const icon = getHealthScoreIcon(healthScore.grade);

    return `<span class="health-score-badge ${gradeClass}" title="${healthScore.details || ''}" style="margin-top: 0.5rem;">
        <span class="health-score-icon">${icon}</span>
        <span>${healthScore.grade} ${healthScore.score}</span>
    </span>`;
}

function getHealthScoreIcon(grade) {
    const icons = {
        'A': '🥗',
        'B': '🥙',
        'C': '🍔',
        'D': '🍕',
        'F': '🍰'
    };
    return icons[grade] || '🍽️';
}

// Store current recipe being added
let pendingRecipeId = null;
let currentShoppingList = []; // Store shopping list data for copy/print

async function addToPlan(recipeId) {
    // Find recipe to get default servings
    const recipe = allRecipes.find(r => r.id === recipeId);
    const defaultServings = recipe && recipe.servings ? parseInt(recipe.servings.toString().match(/\d+/)?.[0] || 1) : 1;

    // Store the recipe ID for later confirmation
    pendingRecipeId = recipeId;

    // Open the servings modal
    document.getElementById('servingsRecipeName').textContent = recipe.title;
    document.getElementById('servingsInput').value = defaultServings;
    document.getElementById('servingsModal').style.display = 'flex';
}

function adjustModalServings(delta) {
    const input = document.getElementById('servingsInput');
    const newValue = Math.max(1, parseInt(input.value || 1) + delta);
    input.value = newValue;
}

function closeServingsModal() {
    document.getElementById('servingsModal').style.display = 'none';
    pendingRecipeId = null;
}

async function confirmServings() {
    if (!pendingRecipeId) return;

    const servings = parseInt(document.getElementById('servingsInput').value) || 1;

    try {
        const response = await fetch('/api/planner/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                recipe_id: pendingRecipeId,
                servings: servings
            })
        });

        const data = await response.json();

        if (data.success) {
            closeServingsModal();
            await loadCurrentPlan();
            displayAvailableRecipes();
        } else {
            alert('Failed to add recipe: ' + data.message);
        }
    } catch (error) {
        alert('Error adding recipe: ' + error.message);
    }
}

async function removeFromPlan(recipeId) {
    try {
        const response = await fetch('/api/planner/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_id: recipeId })
        });

        const data = await response.json();

        if (data.success) {
            await loadCurrentPlan();
            displayAvailableRecipes();
        } else {
            alert('Failed to remove recipe: ' + data.message);
        }
    } catch (error) {
        alert('Error removing recipe: ' + error.message);
    }
}

async function clearPlan() {
    if (!confirm('Are you sure you want to clear the entire plan?')) {
        return;
    }

    try {
        const response = await fetch('/api/planner/clear', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            await loadCurrentPlan();
            displayAvailableRecipes();
        } else {
            alert('Failed to clear plan: ' + data.message);
        }
    } catch (error) {
        alert('Error clearing plan: ' + error.message);
    }
}

async function generateShoppingList() {
    if (currentPlan.length === 0) {
        alert('Add some recipes to your plan first!');
        return;
    }

    try {
        const response = await fetch('/api/planner/shopping-list');
        const data = await response.json();

        if (data.success) {
            displayShoppingList(data.shopping_list);
        } else {
            alert('Failed to generate shopping list: ' + data.message);
        }
    } catch (error) {
        alert('Error generating shopping list: ' + error.message);
    }
}

function convertToMetric(ingredient) {
    let converted = ingredient;

    // Cup conversions
    converted = converted.replace(/(\d+\.?\d*)\s*cups?\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 240);
        return `${ml}ml `;
    });

    // Tablespoon conversions
    converted = converted.replace(/(\d+\.?\d*)\s*(tbsp?|tablespoons?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 15);
        return `${ml}ml `;
    });

    // Teaspoon conversions
    converted = converted.replace(/(\d+\.?\d*)\s*(tsp?|teaspoons?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 5);
        return `${ml}ml `;
    });

    // Ounce (fluid) conversions
    converted = converted.replace(/(\d+\.?\d*)\s*(fl\.?\s*oz|fluid ounces?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 30);
        return `${ml}ml `;
    });

    // Ounce (weight) conversions
    converted = converted.replace(/(\d+\.?\d*)\s*oz\s+/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 28);
        return `${g}g `;
    });

    // Pound conversions
    converted = converted.replace(/(\d+\.?\d*)\s*(lbs?|pounds?)\s+/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 454);
        if (g >= 1000) {
            return `${(g / 1000).toFixed(1)}kg `;
        }
        return `${g}g `;
    });

    // Fahrenheit to Celsius (for temperatures)
    converted = converted.replace(/(\d+)\s*°?\s*F\b/gi, (match, temp) => {
        const celsius = Math.round((parseFloat(temp) - 32) * 5 / 9);
        return `${celsius}°C`;
    });

    return converted;
}

function displayShoppingList(shoppingList) {
    const content = document.getElementById('shoppingListContent');

    // Store for copy/print functionality
    currentShoppingList = shoppingList;

    if (!shoppingList || shoppingList.length === 0) {
        content.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">No ingredients in your plan yet.</p>';
        document.getElementById('shoppingListModal').style.display = 'flex';
        return;
    }

    let html = '<div class="shopping-list">';

    shoppingList.forEach(item => {
        html += `<div class="shopping-list-section">`;
        html += `<h3>${escapeHtml(item.recipe)}</h3>`;
        html += `<ul class="shopping-list-items">`;

        item.ingredients.forEach(ing => {
            const metricIng = convertToMetric(ing);
            html += `<li><label><input type="checkbox"> ${escapeHtml(metricIng)}</label></li>`;
        });

        html += `</ul></div>`;
    });

    html += '</div>';

    content.innerHTML = html;
    document.getElementById('shoppingListModal').style.display = 'flex';
}

function closeModal() {
    closeShoppingListModal();
}

function closeShoppingListModal() {
    document.getElementById('shoppingListModal').style.display = 'none';
}

function printShoppingList() {
    window.print();
}

async function copyShoppingList() {
    let text = 'SHOPPING LIST\n\n';

    currentShoppingList.forEach(item => {
        if (item.ingredients && item.ingredients.length > 0) {
            text += `${item.recipe}\n`;
            item.ingredients.forEach(ing => {
                const metricIng = convertToMetric(ing);
                text += `  ☐ ${metricIng}\n`;
            });
            text += '\n';
        }
    });

    try {
        await navigator.clipboard.writeText(text);
        alert('Shopping list copied to clipboard!');
    } catch (error) {
        alert('Failed to copy: ' + error.message);
    }
}

function formatTime(minutes) {
    if (!minutes) return '';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to get translated content from recipe
function getTranslatedContent(recipe) {
    if (!recipe.translations || Object.keys(recipe.translations).length === 0) {
        return null; // No translations available
    }

    // Try to get Spanish translation first, then French
    const translation = recipe.translations['es'] || recipe.translations['fr'];
    return translation ? translation.content : null;
}

// Helper function to get translated ingredients
function getTranslatedIngredients(recipe) {
    if (!recipe.translations || Object.keys(recipe.translations).length === 0) {
        return recipe.ingredients || [];
    }

    const translation = recipe.translations['es'] || recipe.translations['fr'];
    return translation && translation.ingredients ? translation.ingredients : (recipe.ingredients || []);
}

// Recipe detail modal functions - consistent with library.js
async function showRecipeDetail(recipeId) {
    try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        const data = await response.json();

        if (data.success) {
            const recipe = data.recipe;
            const modal = document.getElementById('recipeModal');
            const content = document.getElementById('modalContent');

            // Store recipe data
            window.currentRecipeData = recipe;
            window.originalServings = parseServings(recipe.servings);
            window.currentServings = window.originalServings;
            window.selectedLanguage = 'original';

            // Get available translations
            const availableLanguages = getAvailableLanguages(recipe);
            const languageOptions = buildLanguageSelector(availableLanguages);

            // Build nutrition section
            const nutritionHtml = buildNutritionSection(recipe);

            content.innerHTML = `
                <div class="recipe-detail-new">
                    <div class="recipe-header">
                        <h2>${escapeHtml(recipe.title)}</h2>
                        <div class="recipe-meta-row">
                            ${recipe.total_time ? `<span class="meta-item">⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                            ${recipe.servings ? `<span class="meta-item">🍽️ ${escapeHtml(recipe.servings)}</span>` : ''}
                            ${recipe.average_rating ? `<span class="meta-item">${renderStarRating(recipe.average_rating, true, recipe.rating_count)}</span>` : ''}
                        </div>
                    </div>

                    ${recipe.image_url ? `<img src="${recipe.image_url}" class="recipe-detail-image" alt="${recipe.title}">` : ''}

                    <div class="recipe-actions-bar">
                        <div class="language-selector-inline">
                            <label for="recipeLanguageSelect">🌍 Language:</label>
                            <select id="recipeLanguageSelect" onchange="switchRecipeLanguage()">
                                ${languageOptions}
                            </select>
                        </div>
                        <div class="action-buttons">
                            <button id="unitToggleBtn" onclick="toggleUnitSystem()" class="btn btn-outline btn-sm" title="Switch unit system">${window.unitSystem === 'metric' ? '📏 Metric' : '📐 Imperial'}</button>
                            <button onclick="closeRecipeModal()" class="btn btn-secondary btn-sm">Close</button>
                        </div>
                    </div>

                    <div class="recipe-main-tabs">
                        <button class="main-tab active" data-tab="recipe" onclick="switchMainTab('recipe')">📖 Recipe</button>
                        <button class="main-tab" data-tab="rating" onclick="switchMainTab('rating')">⭐ Rating & Notes</button>
                        <button class="main-tab" data-tab="nutrition" onclick="switchMainTab('nutrition')">🥗 Nutrition</button>
                        <button class="main-tab" data-tab="translations" onclick="switchMainTab('translations')">🌍 Translations</button>
                    </div>

                    <div class="tab-panel active" id="recipe-panel">
                        <div class="servings-adjuster-section">
                            ${recipe.servings ? buildServingsAdjuster(recipe.servings) : ''}
                        </div>

                        <div id="ingredientsSection" class="ingredients-section">
                            ${buildIngredientsListHtml(recipe, window.currentServings)}
                        </div>

                        <div id="instructionsSection" class="instructions-section">
                            ${buildInstructionsHtml(recipe)}
                        </div>
                    </div>

                    <div class="tab-panel" id="rating-panel" style="display: none;">
                        ${buildRatingSection(recipe)}
                    </div>

                    <div class="tab-panel" id="nutrition-panel" style="display: none;">
                        ${nutritionHtml}
                    </div>

                    <div class="tab-panel" id="translations-panel" style="display: none;">
                        ${buildTranslationsSection(recipe)}
                    </div>
                </div>
            `;

            modal.style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading recipe:', error);
        alert('Error loading recipe: ' + error.message);
    }
}

function getAvailableLanguages(recipe) {
    const languages = [{ code: 'original', name: 'Original (English)' }];

    if (recipe.translations) {
        const languageMap = {
            'es': 'Spanish 🇪🇸',
            'fr': 'French 🇫🇷',
            'de': 'German 🇩🇪',
            'it': 'Italian 🇮🇹',
            'pt': 'Portuguese 🇵🇹',
            'nl': 'Dutch 🇳🇱',
            'ja': 'Japanese 🇯🇵',
            'zh': 'Chinese 🇨🇳',
            'ko': 'Korean 🇰🇷'
        };

        Object.keys(recipe.translations).forEach(code => {
            languages.push({
                code: code,
                name: languageMap[code] || code.toUpperCase()
            });
        });
    }

    return languages;
}

function buildLanguageSelector(languages) {
    return languages.map(lang =>
        `<option value="${lang.code}">${lang.name}</option>`
    ).join('');
}

function getIngredientsForLanguage(recipe, language) {
    if (language === 'original' || !language) {
        return recipe.ingredients || [];
    }

    if (recipe.translations && recipe.translations[language]) {
        return recipe.translations[language].ingredients || recipe.ingredients || [];
    }

    return recipe.ingredients || [];
}

function getInstructionsForLanguage(recipe, language) {
    if (language === 'original' || !language) {
        return recipe.instructions || [];
    }

    if (recipe.translations && recipe.translations[language]) {
        return recipe.translations[language].instructions || recipe.instructions || [];
    }

    return recipe.instructions || [];
}

function buildIngredientsListHtml(recipe, servings) {
    const scale = servings / window.originalServings;
    const ingredients = getIngredientsForLanguage(recipe, window.selectedLanguage);
    const scaledIngredients = scaleIngredients(ingredients, scale);

    let html = `<div class="collapsible-section">
        <h3 class="collapsible-header" onclick="toggleCollapsible(this)">
            <span>Ingredients</span>
            <svg class="collapse-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </h3>
        <div class="collapsible-content">
            <ul class="ingredients-list">`;
    scaledIngredients.forEach(ing => {
        const convertedIng = convertUnits(ing);
        html += `<li class="ingredient-item"><span class="ingredient-text">${escapeHtml(convertedIng)}</span></li>`;
    });
    html += `</ul>
        </div>
    </div>`;
    return html;
}

function buildInstructionsHtml(recipe) {
    const instructions = getInstructionsForLanguage(recipe, window.selectedLanguage);

    let html = `<div class="collapsible-section">
        <h3 class="collapsible-header" onclick="toggleCollapsible(this)">
            <span>Instructions</span>
            <svg class="collapse-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </h3>
        <div class="collapsible-content">`;
    if (instructions && instructions.length > 0) {
        html += '<ol class="instructions-list">';
        instructions.forEach(inst => {
            const convertedInst = convertUnits(inst);
            html += `<li>${escapeHtml(convertedInst)}</li>`;
        });
        html += '</ol>';
    } else {
        html += '<p style="color: var(--text-secondary);">No instructions available</p>';
    }
    html += `</div>
    </div>`;
    return html;
}

// Toggle collapsible section
function toggleCollapsible(header) {
    const section = header.parentElement;
    section.classList.toggle('collapsed');
}

function switchRecipeLanguage() {
    const language = document.getElementById('recipeLanguageSelect').value;
    window.selectedLanguage = language;

    // Update ingredients
    const ingredientsSection = document.getElementById('ingredientsSection');
    if (ingredientsSection) {
        ingredientsSection.innerHTML = buildIngredientsListHtml(window.currentRecipeData, window.currentServings);
    }

    // Update instructions
    const instructionsSection = document.getElementById('instructionsSection');
    if (instructionsSection) {
        instructionsSection.innerHTML = buildInstructionsHtml(window.currentRecipeData);
    }
}

function closeRecipeModal() {
    document.getElementById('recipeModal').style.display = 'none';
}

function switchMainTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    document.getElementById(`${tabName}-panel`).style.display = 'block';
}

function buildNutritionSection(recipe) {
    let html = '';

    // Get servings count for per-serving calculation
    const servings = parseServings(recipe.servings) || 1;

    // Health Score section
    if (recipe.health_score && recipe.health_score.grade) {
        html += `
            <div class="nutrition-health-score">
                <h3>Health Score</h3>
                <div class="health-score-display">
                    <span class="health-score-badge grade-${recipe.health_score.grade.toLowerCase()}">
                        ${getHealthScoreIcon(recipe.health_score.grade)} ${recipe.health_score.grade} ${recipe.health_score.score}
                    </span>
                    <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.5rem;">${recipe.health_score.details || ''}</p>
                </div>
            </div>
        `;
    }

    // Nutrition macros section
    if (recipe.nutrition && Object.keys(recipe.nutrition).length > 0) {
        const nutrition = recipe.nutrition;

        html += `
            <div class="nutrition-macros">
                <h3>Nutrition Facts <span style="font-weight: normal; font-size: 0.875rem; color: var(--text-secondary);">(per serving)</span></h3>
                <div class="macros-grid">
        `;

        const macroConfig = [
            { key: 'calories', label: 'Calories', unit: 'kcal', icon: '🔥' },
            { key: 'protein', label: 'Protein', unit: 'g', icon: '💪' },
            { key: 'carbohydrates', altKey: 'carbs', label: 'Carbohydrates', unit: 'g', icon: '🍞' },
            { key: 'fat', altKey: 'totalFat', label: 'Fat', unit: 'g', icon: '🧈' },
            { key: 'saturatedFat', label: 'Saturated Fat', unit: 'g', icon: '🥓' },
            { key: 'fiber', altKey: 'dietaryFiber', label: 'Fiber', unit: 'g', icon: '🥬' },
            { key: 'sugar', label: 'Sugar', unit: 'g', icon: '🍬' },
            { key: 'sodium', label: 'Sodium', unit: 'mg', icon: '🧂' },
            { key: 'cholesterol', label: 'Cholesterol', unit: 'mg', icon: '🫀' },
            { key: 'potassium', label: 'Potassium', unit: 'mg', icon: '🍌' }
        ];

        let hasMacros = false;
        macroConfig.forEach(macro => {
            let value = nutrition[macro.key];
            if (value === undefined && macro.altKey) {
                value = nutrition[macro.altKey];
            }

            if (value !== undefined && value !== null && value !== '') {
                hasMacros = true;
                // Calculate per-serving value
                let numValue = typeof value === 'number' ? value : parseFloat(value);
                if (!isNaN(numValue)) {
                    numValue = numValue / servings;
                    // Round to 1 decimal place
                    numValue = Math.round(numValue * 10) / 10;
                }
                const displayValue = isNaN(numValue) ? value : numValue;
                html += `
                    <div class="macro-item">
                        <span class="macro-icon">${macro.icon}</span>
                        <span class="macro-label">${macro.label}</span>
                        <span class="macro-value">${displayValue}${macro.unit}</span>
                    </div>
                `;
            }
        });

        if (!hasMacros) {
            html += '<p style="color: var(--text-secondary); grid-column: 1 / -1;">No detailed nutrition data available</p>';
        }

        html += `
                </div>
            </div>
        `;
    } else if (!recipe.health_score) {
        html += '<p style="color: var(--text-secondary);">No nutrition information available</p>';
    }

    return html;
}

function parseServings(servingsStr) {
    if (!servingsStr) return 1;
    const match = servingsStr.toString().match(/\d+/);
    return match ? parseInt(match[0]) : 1;
}

function buildServingsAdjuster(servings) {
    const currentServings = window.currentServings || parseServings(servings);
    return `
        <span class="servings-adjuster">
            <span>🍽️</span>
            <button class="servings-btn" onclick="adjustServings(-1)" title="Decrease servings">−</button>
            <span id="servingsDisplay">${currentServings}</span>
            <button class="servings-btn" onclick="adjustServings(1)" title="Increase servings">+</button>
            <span style="color: var(--text-secondary); font-size: 0.875rem; margin-left: 0.25rem;">servings</span>
        </span>
    `;
}

function buildIngredientsHtml(recipe, currentServings, useOriginal = false) {
    let html = '';
    const ingredientsList = useOriginal ? recipe.ingredients : recipe.ingredients;

    if (ingredientsList && ingredientsList.length > 0) {
        const originalList = useOriginal ? window.originalIngredientsOriginal : window.originalIngredientsTranslated;
        const scale = currentServings / window.originalServings;
        const scaledIngredients = scaleIngredients(originalList, scale);

        html = '<div class="ingredients-section" id="ingredientsSection"><h3>Ingredients</h3><ul class="ingredients-list">';
        scaledIngredients.forEach((ing) => {
            html += `<li class="ingredient-item"><span class="ingredient-text">${escapeHtml(ing)}</span></li>`;
        });
        html += '</ul></div>';
    }
    return html;
}

function scaleIngredients(ingredients, scale) {
    if (scale === 1) return ingredients;

    return ingredients.map(ing => {
        return ing.replace(/(\d+\.?\d*|\d*\s*\/\s*\d+)/g, (match) => {
            let num;
            if (match.includes('/')) {
                const [numerator, denominator] = match.split('/').map(s => parseFloat(s.trim()));
                num = numerator / denominator;
            } else {
                num = parseFloat(match);
            }
            const scaled = num * scale;
            return parseFloat(scaled.toFixed(2)).toString();
        });
    });
}

function adjustServings(delta) {
    const newServings = Math.max(1, window.currentServings + delta);
    window.currentServings = newServings;

    document.getElementById('servingsDisplay').textContent = newServings;

    // Update ingredients with new serving size
    const ingredientsSection = document.getElementById('ingredientsSection');
    if (ingredientsSection && window.currentRecipeData) {
        ingredientsSection.innerHTML = buildIngredientsListHtml(window.currentRecipeData, newServings);
    }
}

function formatRecipeContent(markdown) {
    let html = markdown;

    // Headers
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Lists
    html = html.replace(/^[-•] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Wrap list items
    const lines = html.split('\n');
    let result = [];
    let inList = false;
    let listType = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const nextLine = i < lines.length - 1 ? lines[i + 1] : '';

        if (line.trim().startsWith('<li>')) {
            if (!inList) {
                const originalLine = markdown.split('\n')[i];
                listType = /^\d+\./.test(originalLine) ? 'ol' : 'ul';
                result.push(`<${listType}>`);
                inList = true;
            }
            result.push(line);

            if (!nextLine.trim().startsWith('<li>')) {
                result.push(`</${listType}>`);
                inList = false;
            }
        } else {
            if (inList && line.trim() === '') {
                result.push(`</${listType}>`);
                inList = false;
            }
            result.push(line);
        }
    }

    if (inList) {
        result.push(`</${listType}>`);
    }

    html = result.join('\n');

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(\s*<[huo])/g, '$1');
    html = html.replace(/(<\/[huo][^>]*>)\s*<\/p>/g, '$1');

    return html;
}

