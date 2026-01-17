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
            <div class="plan-item-content">
                ${recipe.image_url ? `<img src="${recipe.image_url}" class="plan-item-image" alt="${recipe.title_translated}">` : ''}
                <div class="plan-item-details">
                    <h3>${escapeHtml(recipe.title_translated || recipe.title_original)}</h3>
                    <div class="plan-item-meta">
                        ${recipe.total_time ? `<span>⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                        ${recipe.servings ? `<span>🍽️ ${escapeHtml(recipe.servings)}</span>` : ''}
                    </div>
                </div>
            </div>
            <button onclick="removeFromPlan(${recipe.id})" class="btn-remove" title="Remove from plan">
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

        return (recipe.title_translated?.toLowerCase().includes(searchTerm) ||
                recipe.title_original?.toLowerCase().includes(searchTerm));
    });

    const grid = document.getElementById('availableRecipes');

    if (filtered.length === 0) {
        grid.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">No recipes available</p>';
        return;
    }

    grid.innerHTML = filtered.map(recipe => `
        <div class="available-recipe-card">
            ${recipe.image_url ? `<img src="${recipe.image_url}" class="available-recipe-image" alt="${recipe.title_translated}">` : '<div class="available-recipe-placeholder">No Image</div>'}
            <div class="available-recipe-content">
                <h4>${escapeHtml(recipe.title_translated || recipe.title_original)}</h4>
                ${recipe.total_time ? `<span class="recipe-time">⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
            </div>
            <button onclick="addToPlan(${recipe.id})" class="btn btn-primary btn-sm">Add to Plan</button>
        </div>
    `).join('');
}

async function addToPlan(recipeId) {
    try {
        const response = await fetch('/api/planner/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_id: recipeId })
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
        if (recipe.ingredients_translated && recipe.ingredients_translated.length > 0) {
            allIngredients.push({
                recipe: recipe.title_translated || recipe.title_original,
                ingredients: recipe.ingredients_translated
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
        if (recipe.ingredients_translated && recipe.ingredients_translated.length > 0) {
            text += `${recipe.title_translated || recipe.title_original}\n`;
            recipe.ingredients_translated.forEach(ing => {
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
