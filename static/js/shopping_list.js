/**
 * Shopping List Page functionality
 */

let currentShoppingList = [];
let currentCombinedList = [];
let currentView = 'combined'; // 'combined' or 'recipe'

document.addEventListener('DOMContentLoaded', () => {
    // Set up view toggle buttons
    document.getElementById('viewCombined')?.addEventListener('click', () => switchView('combined'));
    document.getElementById('viewByRecipe')?.addEventListener('click', () => switchView('recipe'));

    // Load the combined list by default
    loadCombinedShoppingList();
});

function switchView(view) {
    currentView = view;

    // Update toggle buttons
    document.getElementById('viewCombined')?.classList.toggle('active', view === 'combined');
    document.getElementById('viewByRecipe')?.classList.toggle('active', view === 'recipe');

    // Show appropriate content
    if (view === 'combined') {
        displayCombinedList(currentCombinedList);
    } else {
        displayByRecipeList(currentShoppingList);
    }
}

async function loadCombinedShoppingList() {
    const content = document.getElementById('shoppingListContent');
    content.innerHTML = `
        <div style="text-align: center; padding: 3rem;">
            <div class="spinner" style="margin: 0 auto 1rem;"></div>
            <p>Generating shopping list...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/planner/shopping-list/combined');
        const data = await response.json();

        if (data.success) {
            currentCombinedList = data.combined_list || [];
            currentShoppingList = data.by_recipe || [];

            if (currentView === 'combined') {
                displayCombinedList(currentCombinedList);
            } else {
                displayByRecipeList(currentShoppingList);
            }
        } else {
            showError('Failed to load shopping list: ' + data.message);
        }
    } catch (error) {
        showError('Error loading shopping list: ' + error.message);
    }
}

function displayCombinedList(combinedList) {
    const content = document.getElementById('shoppingListContent');

    if (!combinedList || combinedList.length === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 4rem 2rem;">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 1.5rem; opacity: 0.3;">
                    <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2 5m2-5h10m0 0l2 5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">No Items Yet</h3>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Add recipes to your weekly plan to generate a shopping list</p>
                <a href="/planner" class="btn btn-primary">Go to Weekly Planner</a>
            </div>
        `;
        return;
    }

    let html = '<div class="shopping-list">';
    html += '<div class="shopping-list-section">';
    html += '<div class="shopping-list-header">';
    html += '<h3>Total Shopping List</h3>';
    html += `<span class="item-count">${combinedList.length} items</span>`;
    html += '</div>';
    html += '<ul class="shopping-list-items combined-list">';

    combinedList.forEach((item, index) => {
        const displayText = item.display || item.item || item;
        html += `<li>
                    <label>
                        <input type="checkbox" id="combined-${index}">
                        <span class="ingredient-text">${escapeHtml(convertToMetric(displayText))}</span>
                    </label>
                 </li>`;
    });

    html += '</ul></div></div>';

    content.innerHTML = html;
    restoreCheckedItems();
}

function displayByRecipeList(shoppingList) {
    const content = document.getElementById('shoppingListContent');

    if (!shoppingList || shoppingList.length === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 4rem 2rem;">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 1.5rem; opacity: 0.3;">
                    <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2 5m2-5h10m0 0l2 5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">No Items Yet</h3>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Add recipes to your weekly plan to generate a shopping list</p>
                <a href="/planner" class="btn btn-primary">Go to Weekly Planner</a>
            </div>
        `;
        return;
    }

    let html = '<div class="shopping-list">';

    shoppingList.forEach((item, index) => {
        const recipeTitle = item.recipe || 'Recipe';
        const ingredients = item.ingredients || [];

        html += `<div class="shopping-list-section">`;
        html += `<div class="shopping-list-header">`;
        html += `<h3>${escapeHtml(recipeTitle)}</h3>`;
        html += `<button onclick="toggleRecipe(${index})" class="btn-collapse" id="toggle-${index}" aria-label="Toggle section">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 8l4 4 4-4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                 </button>`;
        html += `</div>`;
        html += `<ul class="shopping-list-items" id="items-${index}">`;

        ingredients.forEach((ing, ingIndex) => {
            html += `<li>
                        <label>
                            <input type="checkbox" id="check-${index}-${ingIndex}">
                            <span class="ingredient-text">${escapeHtml(convertToMetric(ing))}</span>
                        </label>
                     </li>`;
        });

        html += `</ul></div>`;
    });

    html += '</div>';

    content.innerHTML = html;
    restoreCheckedItems();
}

function toggleRecipe(index) {
    const items = document.getElementById(`items-${index}`);
    const toggle = document.getElementById(`toggle-${index}`);

    if (items.style.display === 'none') {
        items.style.display = 'block';
        toggle.classList.remove('collapsed');
    } else {
        items.style.display = 'none';
        toggle.classList.add('collapsed');
    }
}

function restoreCheckedItems() {
    const checked = JSON.parse(localStorage.getItem('shoppingListChecked') || '{}');

    Object.keys(checked).forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox && checked[id]) {
            checkbox.checked = true;
            checkbox.parentElement.classList.add('checked');
        }
    });

    // Add event listeners for checkboxes
    document.querySelectorAll('.shopping-list-items input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const checked = JSON.parse(localStorage.getItem('shoppingListChecked') || '{}');
            checked[e.target.id] = e.target.checked;
            localStorage.setItem('shoppingListChecked', JSON.stringify(checked));

            if (e.target.checked) {
                e.target.parentElement.classList.add('checked');
            } else {
                e.target.parentElement.classList.remove('checked');
            }
        });
    });
}

async function copyShoppingList() {
    let text = '🛒 SHOPPING LIST\n\n';

    if (currentView === 'combined' && currentCombinedList.length > 0) {
        text += '=== TOTAL LIST ===\n';
        currentCombinedList.forEach(item => {
            const displayText = item.display || item.item || item;
            text += `☐ ${displayText}\n`;
        });
    } else if (currentShoppingList.length > 0) {
        currentShoppingList.forEach(item => {
            if (item.ingredients && item.ingredients.length > 0) {
                text += `${item.recipe}\n`;
                item.ingredients.forEach(ing => {
                    text += `  ☐ ${convertToMetric(ing)}\n`;
                });
                text += '\n';
            }
        });
    }

    try {
        await navigator.clipboard.writeText(text);
        showSuccess('Shopping list copied to clipboard!');
    } catch (error) {
        alert('Failed to copy: ' + error.message);
    }
}

function printShoppingList() {
    window.print();
}

function showError(message) {
    const content = document.getElementById('shoppingListContent');
    content.innerHTML = `
        <div style="text-align: center; padding: 3rem 2rem; color: var(--error-color);">
            <p>${escapeHtml(message)}</p>
            <button onclick="loadCombinedShoppingList()" class="btn btn-primary" style="margin-top: 1rem;">Retry</button>
        </div>
    `;
}

function showSuccess(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
