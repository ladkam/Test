/**
 * Weekly Planner functionality
 */

let currentPlan = [];
let allRecipes = [];

document.addEventListener('DOMContentLoaded', () => {
    loadCurrentPlan();
    loadAvailableRecipes();

    // Event listeners
    document.getElementById('searchRecipes').addEventListener('input', filterAvailableRecipes);
    document.getElementById('generateShoppingList').addEventListener('click', generateShoppingList);
    document.getElementById('clearPlan').addEventListener('click', clearPlan);
    document.querySelector('.close').addEventListener('click', closeModal);
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

    planList.innerHTML = currentPlan.map(recipe => `
        <div class="plan-item">
            <div class="plan-item-content" onclick="showRecipeDetail(${recipe.id})" style="cursor: pointer;">
                ${recipe.image_url ? `<img src="${recipe.image_url}" class="plan-item-image" alt="${recipe.title}">` : ''}
                <div class="plan-item-details">
                    <h3>${escapeHtml(recipe.title)}</h3>
                    <div class="plan-item-meta">
                        ${recipe.total_time ? `<span>⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                        ${recipe.servings ? `<span>🍽️ ${escapeHtml(recipe.servings)}</span>` : ''}
                    </div>
                </div>
            </div>
            <button onclick="event.stopPropagation(); removeFromPlan(${recipe.id})" class="btn-remove" title="Remove from plan">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    `).join('');
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

    grid.innerHTML = filtered.map(recipe => `
        <div class="available-recipe-card">
            ${recipe.image_url ? `<img src="${recipe.image_url}" class="available-recipe-image" alt="${recipe.title}">` : '<div class="available-recipe-placeholder">No Image</div>'}
            <div class="available-recipe-content">
                <h4>${escapeHtml(recipe.title)}</h4>
                ${recipe.total_time ? `<span class="recipe-time">⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
            </div>
            <button onclick="addToPlan(${recipe.id})" class="btn btn-primary btn-sm">Add to Plan</button>
        </div>
    `).join('');
}

async function addToPlan(recipeId) {
    // Find recipe to get default servings
    const recipe = allRecipes.find(r => r.id === recipeId);
    const defaultServings = recipe && recipe.servings ? parseInt(recipe.servings.toString().match(/\d+/)?.[0] || 1) : 1;

    // Prompt for servings
    const servingsInput = prompt(`How many servings? (Default: ${defaultServings})`, defaultServings);

    if (servingsInput === null) return; // User cancelled

    const servings = parseInt(servingsInput) || defaultServings;

    try {
        const response = await fetch('/api/planner/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                recipe_id: recipeId,
                servings: servings
            })
        });

        const data = await response.json();

        if (data.success) {
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

function displayShoppingList(shoppingList) {
    const content = document.getElementById('shoppingListContent');

    let html = '<div class="shopping-list">';

    // Group by recipe if needed, or just list all ingredients
    const allIngredients = [];
    currentPlan.forEach(recipe => {
        if (recipe.ingredients && recipe.ingredients.length > 0) {
            allIngredients.push({
                recipe: recipe.title,
                ingredients: recipe.ingredients
            });
        }
    });

    allIngredients.forEach(item => {
        html += `<div class="shopping-list-section">`;
        html += `<h3>${escapeHtml(item.recipe)}</h3>`;
        html += `<ul class="shopping-list-items">`;
        item.ingredients.forEach(ing => {
            html += `<li><label><input type="checkbox"> ${escapeHtml(ing)}</label></li>`;
        });
        html += `</ul></div>`;
    });

    html += '</div>';

    content.innerHTML = html;
    document.getElementById('shoppingListModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('shoppingListModal').style.display = 'none';
}

function printShoppingList() {
    window.print();
}

async function copyShoppingList() {
    let text = 'SHOPPING LIST\n\n';

    currentPlan.forEach(recipe => {
        if (recipe.ingredients && recipe.ingredients.length > 0) {
            text += `${recipe.title}\n`;
            recipe.ingredients.forEach(ing => {
                text += `  • ${ing}\n`;
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

// Recipe detail modal functions (shared with library.js)
async function showRecipeDetail(recipeId) {
    try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        const data = await response.json();

        if (data.success) {
            const recipe = data.recipe;
            const modal = document.getElementById('recipeModal');
            const content = document.getElementById('modalContent');

            // Store original recipe data for scaling
            window.currentRecipeData = recipe;
            window.originalServings = parseServings(recipe.servings);
            window.currentServings = window.originalServings;
            window.originalIngredientsTranslated = [...getTranslatedIngredients(recipe)];
            window.originalIngredientsOriginal = [...(recipe.ingredients || [])];
            window.activeLanguageTab = 'translated'; // Track which tab is active

            // Build ingredients section
            let ingredientsHtml = buildIngredientsHtml(recipe, window.currentServings);

            content.innerHTML = `
                <div class="recipe-detail">
                    ${recipe.image_url ? `<img src="${recipe.image_url}" class="recipe-detail-image" alt="${recipe.title}">` : ''}
                    <h2>${escapeHtml(recipe.title)}</h2>

                    <div class="recipe-detail-meta">
                        ${recipe.total_time ? `<span>⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                        ${recipe.servings ? buildServingsAdjuster(recipe.servings) : ''}
                        ${recipe.source_language ? `<span>🌍 ${escapeHtml(recipe.source_language)}</span>` : ''}
                    </div>

                    <div class="recipe-detail-actions">
                        <button onclick="closeRecipeModal()" class="btn btn-secondary">Close</button>
                    </div>

                    ${ingredientsHtml}

                    <div class="recipe-detail-content">
                        <div class="recipe-tabs">
                            <button class="recipe-tab active" data-lang="translated">Translated</button>
                            <button class="recipe-tab" data-lang="original">Original</button>
                        </div>

                        <div class="recipe-tab-content active" id="translated-content">
                            ${formatRecipeContent(getTranslatedContent(recipe) || recipe.content || 'No translation available')}
                        </div>

                        <div class="recipe-tab-content" id="original-content" style="display: none;">
                            ${formatRecipeContent(recipe.content || 'No content available')}
                        </div>
                    </div>
                </div>
            `;

            // Tab switching
            content.querySelectorAll('.recipe-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    const lang = tab.dataset.lang;
                    window.activeLanguageTab = lang; // Track active tab

                    content.querySelectorAll('.recipe-tab').forEach(t => t.classList.remove('active'));
                    content.querySelectorAll('.recipe-tab-content').forEach(c => c.style.display = 'none');
                    tab.classList.add('active');
                    document.getElementById(`${lang}-content`).style.display = 'block';

                    // Update ingredients to match the active tab
                    const useOriginal = lang === 'original';
                    const originalIngredients = useOriginal ? window.originalIngredientsOriginal : window.originalIngredientsTranslated;
                    const scale = window.currentServings / window.originalServings;
                    const scaledIngredients = scaleIngredients(originalIngredients, scale);

                    // Rebuild ingredients list
                    const ingredientsSection = document.getElementById('ingredientsSection');
                    if (ingredientsSection) {
                        let html = '<h3>Ingredients</h3><ul class="ingredients-list">';
                        scaledIngredients.forEach((ing) => {
                            html += `<li class="ingredient-item"><span class="ingredient-text">${escapeHtml(ing)}</span></li>`;
                        });
                        html += '</ul>';
                        ingredientsSection.innerHTML = html;
                    }
                });
            });

            modal.style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading recipe:', error);
        alert('Error loading recipe: ' + error.message);
    }
}

function closeRecipeModal() {
    document.getElementById('recipeModal').style.display = 'none';
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

    // Determine which ingredient list to use based on active tab
    const useOriginal = window.activeLanguageTab === 'original';
    const originalIngredients = useOriginal ? window.originalIngredientsOriginal : window.originalIngredientsTranslated;

    const scale = newServings / window.originalServings;
    const scaledIngredients = scaleIngredients(originalIngredients, scale);

    const ingredientsSection = document.getElementById('ingredientsSection');
    if (ingredientsSection) {
        let html = '<h3>Ingredients</h3><ul class="ingredients-list">';
        scaledIngredients.forEach((ing) => {
            html += `<li class="ingredient-item"><span class="ingredient-text">${escapeHtml(ing)}</span></li>`;
        });
        html += '</ul>';
        ingredientsSection.innerHTML = html;
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

