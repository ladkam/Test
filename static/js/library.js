/**
 * Recipe Library functionality
 */

let allRecipes = [];
let filteredRecipes = [];
let selectedTags = [];
let currentSort = 'newest';
let currentView = 'grid';

// Load recipes on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();

    // Search input with debounce
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterRecipes, 150);
    });

    // Duration filter
    const durationFilter = document.getElementById('durationFilter');
    if (durationFilter) {
        durationFilter.addEventListener('change', filterRecipes);
    }

    // Sort filter
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        sortFilter.addEventListener('change', (e) => {
            currentSort = e.target.value;
            sortRecipes();
            displayRecipes();
        });
    }

    // View toggle buttons
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;
            displayRecipes();
        });
    });

    // Clear filters
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }

    // Modal close
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });

    window.addEventListener('click', (e) => {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // "/" to focus search
        if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            searchInput.focus();
        }
        // Escape to clear search
        if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.value = '';
            filterRecipes();
            searchInput.blur();
        }
    });
});

async function loadRecipes() {
    const grid = document.getElementById('recipeGrid');

    // Show skeleton loaders while loading
    grid.innerHTML = generateSkeletonCards(6);
    grid.style.display = 'grid';

    try {
        const response = await fetch('/api/recipes');
        const data = await response.json();

        if (data.success) {
            allRecipes = data.recipes;
            filteredRecipes = [...allRecipes];
            sortRecipes();
            populateTagFilter();
            displayRecipes();
        } else {
            if (window.toast) {
                window.toast.error('Failed to load recipes');
            }
        }
    } catch (error) {
        if (window.toast) {
            window.toast.error('Error loading recipes: ' + error.message);
        }
    }
}

function generateSkeletonCards(count) {
    return Array(count).fill(0).map(() => `
        <div class="skeleton-card">
            <div class="skeleton-image"></div>
            <div class="skeleton-content">
                <div class="skeleton skeleton-title"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text"></div>
            </div>
        </div>
    `).join('');
}

function sortRecipes() {
    filteredRecipes.sort((a, b) => {
        switch (currentSort) {
            case 'newest':
                return (b.id || 0) - (a.id || 0);
            case 'oldest':
                return (a.id || 0) - (b.id || 0);
            case 'name-asc':
                return (a.title || '').localeCompare(b.title || '');
            case 'name-desc':
                return (b.title || '').localeCompare(a.title || '');
            case 'rating':
                return (b.average_rating || 0) - (a.average_rating || 0);
            case 'time-asc':
                return (a.total_time || 999) - (b.total_time || 999);
            case 'time-desc':
                return (b.total_time || 0) - (a.total_time || 0);
            default:
                return 0;
        }
    });
}

function filterRecipes() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    const durationFilterEl = document.getElementById('durationFilter');
    const durationFilter = durationFilterEl ? durationFilterEl.value : '';

    filteredRecipes = allRecipes.filter(recipe => {
        // Search filter - search in title, ingredients, and tags
        const matchesSearch = !searchTerm ||
            recipe.title?.toLowerCase().includes(searchTerm) ||
            (recipe.ingredients || []).some(ing => ing.toLowerCase().includes(searchTerm)) ||
            (recipe.tags || []).some(tag => tag.toLowerCase().includes(searchTerm));

        // Duration filter
        let matchesDuration = true;
        if (durationFilter) {
            const totalTime = recipe.total_time || 0;
            if (durationFilter === '0-30') {
                matchesDuration = totalTime > 0 && totalTime <= 30;
            } else if (durationFilter === '30-60') {
                matchesDuration = totalTime > 30 && totalTime <= 60;
            } else if (durationFilter === '60+') {
                matchesDuration = totalTime > 60;
            }
        }

        // Tag filter
        const matchesTags = selectedTags.length === 0 ||
            (recipe.tags && selectedTags.every(tag => recipe.tags.includes(tag)));

        return matchesSearch && matchesDuration && matchesTags;
    });

    sortRecipes();
    displayRecipes();
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('durationFilter').value = '';
    selectedTags = [];
    populateTagFilter(); // Refresh tag buttons
    filterRecipes();
}

function displayRecipes() {
    const grid = document.getElementById('recipeGrid');
    const emptyState = document.getElementById('emptyState');
    const countEl = document.getElementById('recipeCount');

    // Update count
    const count = filteredRecipes.length;
    const total = allRecipes.length;
    if (count === total) {
        countEl.innerHTML = `<strong>${count}</strong> ${count === 1 ? 'recipe' : 'recipes'}`;
    } else {
        countEl.innerHTML = `<strong>${count}</strong> of ${total} recipes`;
    }

    if (filteredRecipes.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    // Apply view class
    grid.className = `recipe-grid ${currentView === 'list' ? 'list-view' : ''}`;
    grid.style.display = 'grid';
    emptyState.style.display = 'none';

    grid.innerHTML = filteredRecipes.map(recipe => createRecipeCard(recipe)).join('');

    // Attach event listeners
    document.querySelectorAll('.recipe-card').forEach(card => {
        const clickable = card.querySelector('.card-clickable');
        if (clickable) {
            clickable.addEventListener('click', () => {
                const recipeId = card.dataset.recipeId;
                showRecipeDetail(recipeId);
            });
        }

        // Quick action buttons
        card.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const recipeId = card.dataset.recipeId;

                if (action === 'delete') {
                    deleteRecipe(recipeId);
                } else if (action === 'edit') {
                    window.location.href = `/recipes/${recipeId}/edit`;
                } else if (action === 'plan') {
                    addToPlan(recipeId);
                }
            });
        });

        const deleteBtn = card.querySelector('.btn-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const recipeId = card.dataset.recipeId;
                deleteRecipe(recipeId);
            });
        }
    });
}

function addToPlan(recipeId) {
    // Redirect to planner with recipe to add
    window.location.href = `/planner?add=${recipeId}`;
}

function createRecipeCard(recipe) {
    const imageUrl = recipe.image_url || '';
    const title = recipe.title || 'Untitled Recipe';
    const time = formatTime(recipe.total_time);
    const ingredients = recipe.ingredients || [];
    const previewIngredients = ingredients.slice(0, 3).map(i => i.split(',')[0]).join(', ');

    // Rating badge
    const ratingBadge = recipe.average_rating ? `
        <span class="recipe-card-badge recipe-card-rating">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            ${recipe.average_rating.toFixed(1)}
        </span>
    ` : '';

    // Time badge
    const timeBadge = time ? `
        <span class="recipe-card-badge recipe-card-badge-time">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            ${time}
        </span>
    ` : '';

    // Tags (show first 2)
    const tags = recipe.tags || [];
    const tagsHtml = tags.length > 0 ? `
        <div class="recipe-card-tags">
            ${tags.slice(0, 2).map(tag => `<span class="tag-badge-sm">${escapeHtml(tag)}</span>`).join('')}
            ${tags.length > 2 ? `<span class="tag-badge-sm tag-more">+${tags.length - 2}</span>` : ''}
        </div>
    ` : '';

    return `
        <div class="recipe-card" data-recipe-id="${recipe.id}">
            <div class="card-clickable">
                <div class="recipe-card-image-container">
                    ${imageUrl
                        ? `<img src="${imageUrl}" alt="${escapeHtml(title)}" class="recipe-card-image" loading="lazy">`
                        : '<div class="recipe-card-image-placeholder"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg></div>'
                    }
                    <div class="recipe-card-badges">
                        <span class="recipe-card-badges-left">${timeBadge}</span>
                        <span class="recipe-card-badges-right">${ratingBadge}</span>
                    </div>
                    <div class="recipe-card-overlay">
                        <div class="recipe-card-quick-actions">
                            <button class="btn btn-sm" data-action="edit" title="Edit recipe">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                Edit
                            </button>
                            <button class="btn btn-sm" data-action="plan" title="Add to meal plan">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="12" y1="14" x2="12" y2="18"/><line x1="10" y1="16" x2="14" y2="16"/></svg>
                                Plan
                            </button>
                        </div>
                    </div>
                </div>
                <div class="recipe-card-content">
                    <h3 class="recipe-card-title">${escapeHtml(title)}</h3>
                    ${tagsHtml}
                    ${previewIngredients ? `<p class="recipe-card-preview">${escapeHtml(previewIngredients)}...</p>` : ''}
                </div>
            </div>
            <div class="recipe-card-actions">
                <button class="btn-delete" title="Delete recipe" data-action="delete">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
}

function getHealthScoreBadge(healthScore) {
    if (!healthScore || !healthScore.grade || !healthScore.score) {
        return '';
    }

    const gradeClass = `grade-${healthScore.grade.toLowerCase()}`;
    const icon = getHealthScoreIcon(healthScore.grade);

    return `<span class="health-score-badge ${gradeClass}" title="${healthScore.details || ''}">
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
        'F': '�'
    };
    return icons[grade] || '🍽️';
}

function getNutritionBadges(nutrition) {
    if (!nutrition || typeof nutrition !== 'object') {
        return '';
    }

    const badges = [];

    // Extract and parse nutrition values
    const parseValue = (val) => {
        if (!val) return null;
        const num = typeof val === 'string' ? parseFloat(val.replace(/[^\d.]/g, '')) : parseFloat(val);
        return isNaN(num) ? null : Math.round(num);
    };

    const calories = parseValue(nutrition.calories);
    const protein = parseValue(nutrition.protein);
    const carbs = parseValue(nutrition.carbohydrates || nutrition.carbs);
    const fat = parseValue(nutrition.fat || nutrition.totalFat);

    if (calories) badges.push(`<span class="nutrition-badge">⚡ ${calories} cal</span>`);
    if (protein) badges.push(`<span class="nutrition-badge">🥩 ${protein}g P</span>`);
    if (carbs) badges.push(`<span class="nutrition-badge">🌾 ${carbs}g C</span>`);
    if (fat) badges.push(`<span class="nutrition-badge">🥑 ${fat}g F</span>`);

    return badges.length > 0 ? `<div class="recipe-nutrition-badges">${badges.join('')}</div>` : '';
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

        // Define macro display order and formatting
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
            { key: 'potassium', label: 'Potassium', unit: 'mg', icon: '🍌' },
            { key: 'vitaminA', label: 'Vitamin A', unit: '%', icon: '👁️' },
            { key: 'vitaminC', label: 'Vitamin C', unit: '%', icon: '🍊' },
            { key: 'calcium', label: 'Calcium', unit: '%', icon: '🦴' },
            { key: 'iron', label: 'Iron', unit: '%', icon: '🩸' }
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

function formatTime(minutes) {
    if (!minutes) return '';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

// Helper function to parse servings from string (e.g., "4 servings" -> 4)
function parseServings(servingsStr) {
    if (!servingsStr) return 1;
    const match = servingsStr.toString().match(/\d+/);
    return match ? parseInt(match[0]) : 1;
}

// Build servings adjuster HTML
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

// Build ingredients HTML with current servings scale
function buildIngredientsHtml(recipe, currentServings, useOriginal = false) {
    let html = '';
    const ingredientsList = useOriginal ? recipe.ingredients : recipe.ingredients;

    if (ingredientsList && ingredientsList.length > 0) {
        const originalList = useOriginal ? window.originalIngredientsOriginal : window.originalIngredientsTranslated;
        const scale = currentServings / window.originalServings;
        const scaledIngredients = scaleIngredients(originalList, scale);

        html = '<div class="ingredients-section" id="ingredientsSection"><h3>Ingredients</h3><ul class="ingredients-list">';
        scaledIngredients.forEach(ing => {
            html += `<li class="ingredient-item"><span class="ingredient-text">${escapeHtml(ing)}</span></li>`;
        });
        html += '</ul></div>';
    }
    return html;
}

// Scale ingredients based on servings multiplier
function scaleIngredients(ingredients, scale) {
    if (scale === 1) return ingredients;

    return ingredients.map(ing => {
        // Match numbers (including fractions like 1/2, 1.5, etc.)
        return ing.replace(/(\d+\.?\d*|\d*\s*\/\s*\d+)/g, (match) => {
            let num;
            if (match.includes('/')) {
                // Handle fractions
                const [numerator, denominator] = match.split('/').map(s => parseFloat(s.trim()));
                num = numerator / denominator;
            } else {
                num = parseFloat(match);
            }
            const scaled = num * scale;
            // Round to 2 decimal places and remove trailing zeros
            return parseFloat(scaled.toFixed(2)).toString();
        });
    });
}

// Adjust servings and update ingredients display
function adjustServings(delta) {
    const newServings = Math.max(1, window.currentServings + delta);
    window.currentServings = newServings;

    // Update servings display
    document.getElementById('servingsDisplay').textContent = newServings;

    // Rebuild ingredients list with new servings
    const ingredientsSection = document.getElementById('ingredientsSection');
    if (ingredientsSection && window.currentRecipeData) {
        ingredientsSection.innerHTML = buildIngredientsListHtml(window.currentRecipeData, newServings);
    }
}

// Helper function for rating.js to reload recipe details
function loadRecipeDetails(recipeId) {
    showRecipeDetail(recipeId);
}

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

            // Build nutrition section with all macros
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
                        ${recipe.tags && recipe.tags.length > 0 ? `
                            <div class="recipe-tags" style="margin-top: 0.75rem;">
                                ${recipe.tags.map(tag => `<span class="tag-badge">${escapeHtml(tag)}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${recipe.source_url ? `<a href="${escapeHtml(recipe.source_url)}" target="_blank" rel="noopener noreferrer" class="original-recipe-link">View original recipe</a>` : ''}
                    </div>

                    ${recipe.image_url ? `<img src="${recipe.image_url}" class="recipe-detail-image" alt="${recipe.title}">` : ''}

                    <div class="recipe-actions-bar">
                        <div class="action-buttons">
                            <button onclick="addToWeeklyPlan(${recipe.id})" class="btn btn-primary btn-sm">📅 Add to Plan</button>
                            <button onclick="editRecipe(${recipe.id})" class="btn btn-secondary btn-sm">✏️ Edit</button>
                        </div>
                    </div>

                    <div class="recipe-main-tabs">
                        <button class="main-tab active" data-tab="recipe" onclick="switchMainTab('recipe')">📖 Recipe</button>
                        <button class="main-tab" data-tab="rating" onclick="switchMainTab('rating')">⭐ Rating & Notes</button>
                        <button class="main-tab" data-tab="nutrition" onclick="switchMainTab('nutrition')">🥗 Nutrition</button>
                    </div>

                    <div class="tab-panel active" id="recipe-panel">
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
                </div>
            `;

            modal.style.display = 'flex';
        }
    } catch (error) {
        showError('Error loading recipe: ' + error.message);
    }
}

function buildIngredientsListHtml(recipe, servings) {
    const scale = servings / window.originalServings;
    const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
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
        html += `
            <li class="ingredient-item">
                <span class="ingredient-text">${escapeHtml(ing)}</span>
            </li>
        `;
    });
    html += `</ul>
        </div>
    </div>`;
    return html;
}

function buildInstructionsHtml(recipe) {
    const instructions = Array.isArray(recipe.instructions) ? recipe.instructions : [];

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
            html += `<li>${escapeHtml(inst)}</li>`;
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

function formatRecipeContent(markdown) {
    // Simple markdown to HTML converter (reuse from results.html)
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

            if (!nextLine.trim().startsWith('<li>') && nextLine.trim() !== '') {
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

function closeModal() {
    document.getElementById('recipeModal').style.display = 'none';
}

function editRecipe(recipeId) {
    window.location.href = `/recipe/edit/${recipeId}`;
}

async function addToWeeklyPlan(recipeId) {
    try {
        // Fetch recipe data if not already loaded
        let recipe = window.currentRecipeData;
        if (!recipe || recipe.id !== recipeId) {
            const response = await fetch(`/api/recipes/${recipeId}`);
            const data = await response.json();
            if (!data.success) {
                alert('Failed to load recipe');
                return;
            }
            recipe = data.recipe;
        }

        // Use current servings if adjusted, otherwise use original servings
        const servings = window.currentServings || window.originalServings || parseServings(recipe.servings) || 1;

        // Show confirmation with servings
        const confirmed = confirm(`Add "${recipe.title}" to weekly plan with ${servings} servings?`);

        if (!confirmed) return;

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
            alert('Recipe added to weekly plan!');
            window.location.href = '/planner';
        } else {
            alert('Failed to add recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error adding recipe: ' + error.message);
    }
}

async function deleteRecipe(recipeId) {
    if (!confirm('Are you sure you want to delete this recipe?')) {
        return;
    }

    try {
        const response = await fetch(`/api/recipes/${recipeId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.success) {
            allRecipes = allRecipes.filter(r => r.id !== parseInt(recipeId));
            filterRecipes();
        } else {
            showError(data.message || 'Failed to delete recipe');
        }
    } catch (error) {
        showError('Error deleting recipe: ' + error.message);
    }
}

function populateTagFilter() {
    // Collect all unique tags from recipes
    const allTags = new Set();
    allRecipes.forEach(recipe => {
        if (recipe.tags && Array.isArray(recipe.tags)) {
            recipe.tags.forEach(tag => allTags.add(tag));
        }
    });

    const tagFilterContainer = document.getElementById('tagFilterContainer');
    const tagFilterOptions = document.getElementById('tagFilterOptions');

    if (allTags.size === 0) {
        tagFilterContainer.style.display = 'none';
        return;
    }

    // Show tag filter and populate options
    tagFilterContainer.style.display = 'block';
    tagFilterOptions.innerHTML = Array.from(allTags).sort().map(tag => `
        <button class="tag-filter-btn ${selectedTags.includes(tag) ? 'active' : ''}"
                onclick="toggleTagFilter('${tag.replace(/'/g, "\\'")}')">
            ${escapeHtml(tag)}
        </button>
    `).join('');
}

function toggleTagFilter(tag) {
    const index = selectedTags.indexOf(tag);
    if (index > -1) {
        selectedTags.splice(index, 1);
    } else {
        selectedTags.push(tag);
    }
    populateTagFilter();
    filterRecipes();
}

function showError(message) {
    alert('Error: ' + message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============= Photo Upload & OCR Functions =============

function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
    // Reset state
    currentImageData = null;
    document.getElementById('photoInput').value = '';
    document.querySelector('.upload-prompt').style.display = 'block';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('processImage').disabled = true;
    document.getElementById('processingStatus').style.display = 'none';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file (JPG, PNG, etc.)');
        return;
    }

    // Validate file size (4MB for base64)
    if (file.size > 4 * 1024 * 1024) {
        alert('Image size must be less than 4MB. Please choose a smaller image.');
        return;
    }

    // Read file as base64
    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageData = e.target.result; // This is the base64 data URL

        // Show preview
        document.getElementById('previewImage').src = currentImageData;
        document.querySelector('.upload-prompt').style.display = 'none';
        document.getElementById('imagePreview').style.display = 'block';
        document.getElementById('processImage').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function processImage() {
    if (!currentImageData) return;

    // Hide upload UI, show processing
    document.getElementById('uploadArea').style.display = 'none';
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('processImage').disabled = true;
    document.getElementById('cancelUpload').disabled = true;

    try {
        const response = await fetch('/api/recipes/ocr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: currentImageData
            })
        });

        const data = await response.json();

        if (data.success && data.recipe) {
            // Close upload modal
            closeUploadModal();

            // Open review modal with extracted data
            openReviewModal(data.recipe);
        } else {
            alert('Error extracting recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error processing image: ' + error.message);
    } finally {
        // Reset UI
        document.getElementById('uploadArea').style.display = 'block';
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('processImage').disabled = false;
        document.getElementById('cancelUpload').disabled = false;
    }
}

function openReviewModal(recipeData) {
    // Populate form with extracted data
    document.getElementById('reviewTitle').value = recipeData.title || '';

    // Parse times (convert "15 minutes" to number 15)
    const parseTime = (timeStr) => {
        if (!timeStr) return '';
        const match = timeStr.match(/\d+/);
        return match ? match[0] : '';
    };

    document.getElementById('reviewPrepTime').value = parseTime(recipeData.prep_time);
    document.getElementById('reviewCookTime').value = parseTime(recipeData.cook_time);

    // Join ingredients and instructions as multiline text
    const ingredients = Array.isArray(recipeData.ingredients)
        ? recipeData.ingredients.join('\n')
        : (recipeData.ingredients || '');
    document.getElementById('reviewIngredients').value = ingredients;

    const instructions = Array.isArray(recipeData.instructions)
        ? recipeData.instructions.join('\n')
        : (recipeData.instructions || '');
    document.getElementById('reviewInstructions').value = instructions;

    // Show modal
    document.getElementById('reviewModal').style.display = 'flex';
}

function closeReviewModal() {
    document.getElementById('reviewModal').style.display = 'none';
}

async function saveExtractedRecipe(event) {
    event.preventDefault();

    const title = document.getElementById('reviewTitle').value.trim();
    const prepTime = document.getElementById('reviewPrepTime').value;
    const cookTime = document.getElementById('reviewCookTime').value;
    const ingredientsText = document.getElementById('reviewIngredients').value;
    const instructionsText = document.getElementById('reviewInstructions').value;

    // Parse multiline text to arrays
    const ingredients = ingredientsText.split('\n').map(i => i.trim()).filter(i => i);
    const instructions = instructionsText.split('\n').map(i => i.trim()).filter(i => i);

    if (!title || ingredients.length === 0 || instructions.length === 0) {
        alert('Please fill in the required fields: title, ingredients, and instructions');
        return;
    }

    // Format content from ingredients and instructions
    let contentFormatted = '';
    if (ingredients.length > 0) {
        contentFormatted += '## Ingredients\n\n';
        ingredients.forEach(ing => {
            contentFormatted += `- ${ing}\n`;
        });
        contentFormatted += '\n';
    }

    if (instructions.length > 0) {
        contentFormatted += '## Instructions\n\n';
        instructions.forEach((inst, idx) => {
            contentFormatted += `${idx + 1}. ${inst}\n`;
        });
    }

    // Prepare recipe data
    const recipeData = {
        title: title,
        content: contentFormatted,
        content_original: contentFormatted,
        ingredients: ingredients,
        instructions: instructions,
        prep_time: prepTime ? `${prepTime} minutes` : null,
        cook_time: cookTime ? `${cookTime} minutes` : null,
        total_time: (prepTime && cookTime) ? `${parseInt(prepTime) + parseInt(cookTime)} minutes` : null,
        servings: '',
        image: '',
        url: '',
        author: 'Imported from photo',
    };

    try {
        // Save to library
        const response = await fetch('/api/recipes/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ recipeData })
        });

        const data = await response.json();

        if (data.success) {
            closeReviewModal();
            alert('Recipe saved successfully!');
            loadRecipes();
        } else {
            alert('Error saving recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error saving recipe: ' + error.message);
    }
}
