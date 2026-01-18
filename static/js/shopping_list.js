/**
 * Shopping List Page functionality
 */

let currentShoppingList = [];

document.addEventListener('DOMContentLoaded', () => {
    loadShoppingList();
});

async function loadShoppingList() {
    try {
        const response = await fetch('/api/planner/shopping-list');
        const data = await response.json();

        if (data.success) {
            currentShoppingList = data.shopping_list;
            displayShoppingList(data.shopping_list);
        } else {
            showError('Failed to load shopping list: ' + data.message);
        }
    } catch (error) {
        showError('Error loading shopping list: ' + error.message);
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
        html += `<div class="shopping-list-section">`;
        html += `<div class="shopping-list-header">`;
        html += `<h3>${escapeHtml(item.recipe)}</h3>`;
        html += `<button onclick="toggleRecipe(${index})" class="btn-collapse" id="toggle-${index}" aria-label="Toggle section">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 8l4 4 4-4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                 </button>`;
        html += `</div>`;
        html += `<ul class="shopping-list-items" id="items-${index}">`;

        item.ingredients.forEach((ing, ingIndex) => {
            const metricIng = convertToMetric(ing);
            html += `<li>
                        <label>
                            <input type="checkbox" id="check-${index}-${ingIndex}">
                            <span class="ingredient-text">${escapeHtml(metricIng)}</span>
                        </label>
                     </li>`;
        });

        html += `</ul></div>`;
    });

    html += '</div>';

    content.innerHTML = html;

    // Restore checked state from localStorage
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
            <button onclick="loadShoppingList()" class="btn btn-primary" style="margin-top: 1rem;">Retry</button>
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
