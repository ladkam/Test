/**
 * Recipe Library functionality
 */

let allRecipes = [];
let filteredRecipes = [];

// Load recipes on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();

    // Search input
    document.getElementById('searchInput').addEventListener('input', filterRecipes);

    // Duration filter
    document.getElementById('durationFilter').addEventListener('change', filterRecipes);

    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', clearFilters);

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
});

async function loadRecipes() {
    try {
        const response = await fetch('/api/recipes');
        const data = await response.json();

        if (data.success) {
            allRecipes = data.recipes;
            filteredRecipes = [...allRecipes];
            displayRecipes();
        } else {
            showError('Failed to load recipes');
        }
    } catch (error) {
        showError('Error loading recipes: ' + error.message);
    }
}

function filterRecipes() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const durationFilter = document.getElementById('durationFilter').value;

    filteredRecipes = allRecipes.filter(recipe => {
        // Search filter
        const matchesSearch = !searchTerm ||
            recipe.title?.toLowerCase().includes(searchTerm) ||
            (recipe.ingredients || []).some(ing => ing.toLowerCase().includes(searchTerm));

        // Duration filter
        let matchesDuration = true;
        if (durationFilter) {
            const totalTime = recipe.total_time || 0;
            if (durationFilter === '0-30') {
                matchesDuration = totalTime <= 30;
            } else if (durationFilter === '30-60') {
                matchesDuration = totalTime > 30 && totalTime <= 60;
            } else if (durationFilter === '60+') {
                matchesDuration = totalTime > 60;
            }
        }

        return matchesSearch && matchesDuration;
    });

    displayRecipes();
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('durationFilter').value = '';
    filterRecipes();
}

function displayRecipes() {
    const grid = document.getElementById('recipeGrid');
    const emptyState = document.getElementById('emptyState');
    const countEl = document.getElementById('recipeCount');

    // Update count
    const count = filteredRecipes.length;
    countEl.textContent = `${count} ${count === 1 ? 'recipe' : 'recipes'}`;

    if (filteredRecipes.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    grid.style.display = 'grid';
    emptyState.style.display = 'none';

    grid.innerHTML = filteredRecipes.map(recipe => createRecipeCard(recipe)).join('');

    // Attach event listeners
    document.querySelectorAll('.recipe-card').forEach(card => {
        card.querySelector('.card-clickable').addEventListener('click', () => {
            const recipeId = card.dataset.recipeId;
            showRecipeDetail(recipeId);
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

function createRecipeCard(recipe) {
    const imageUrl = recipe.image_url || '';
    const title = recipe.title;
    const time = formatTime(recipe.total_time);
    const healthScoreHtml = getHealthScoreBadge(recipe.health_score);
    const ratingHtml = recipe.average_rating ? renderStarRating(recipe.average_rating, true, recipe.rating_count) : '';

    return `
        <div class="recipe-card" data-recipe-id="${recipe.id}">
            <div class="card-clickable">
                ${imageUrl ? `<img src="${imageUrl}" alt="${title}" class="recipe-card-image">` : '<div class="recipe-card-image-placeholder">No Image</div>'}
                <div class="recipe-card-content">
                    <h3 class="recipe-card-title">${escapeHtml(title)}</h3>
                    ${time ? `<p class="recipe-card-time">⏱️ ${time}</p>` : ''}
                    ${ratingHtml ? `<div class="recipe-card-rating">${ratingHtml}</div>` : ''}
                    <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                        ${recipe.source_language ? `<span class="recipe-card-lang">${escapeHtml(recipe.source_language)}</span>` : ''}
                        ${healthScoreHtml}
                    </div>
                </div>
            </div>
            <div class="recipe-card-actions">
                <button class="btn-delete" title="Delete recipe">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M2 4h12M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1m2 0v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h10z" stroke="currentColor" stroke-width="1.5"/>
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
        'F': '🍰'
    };
    return icons[grade] || '🍽️';
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
        scaledIngredients.forEach((ing, idx) => {
            const escapedIng = escapeHtml(ing).replace(/'/g, '&apos;');
            html += `
                <li class="ingredient-item">
                    <span class="ingredient-text">${escapeHtml(ing)}</span>
                    <button class="btn-substitute" onclick="substituteIngredient('${escapedIng}', ${recipe.id})" title="Find substitutes">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        Substitute
                    </button>
                </li>
            `;
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
            window.selectedLanguage = 'original'; // Default to original

            // Get available translations
            const availableLanguages = getAvailableLanguages(recipe);
            const languageOptions = buildLanguageSelector(availableLanguages);

            // Build health score display
            const healthScoreHtml = recipe.health_score ? `
                <div class="health-score-display">
                    <span class="health-score-badge grade-${recipe.health_score.grade.toLowerCase()}">
                        ${getHealthScoreIcon(recipe.health_score.grade)} ${recipe.health_score.grade} ${recipe.health_score.score}
                    </span>
                    <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.5rem;">${recipe.health_score.details || ''}</p>
                </div>
            ` : '<p style="color: var(--text-secondary);">No nutrition information available</p>';

            content.innerHTML = `
                <div class="recipe-detail-new">
                    ${recipe.image_url ? `<img src="${recipe.image_url}" class="recipe-detail-image" alt="${recipe.title}">` : ''}

                    <div class="recipe-header">
                        <h2>${escapeHtml(recipe.title)}</h2>
                        <div class="recipe-meta-row">
                            ${recipe.total_time ? `<span class="meta-item">⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                            ${recipe.servings ? `<span class="meta-item">🍽️ ${escapeHtml(recipe.servings)}</span>` : ''}
                            ${recipe.average_rating ? `<span class="meta-item">${renderStarRating(recipe.average_rating, true, recipe.rating_count)}</span>` : ''}
                        </div>
                    </div>

                    <div class="recipe-actions-bar">
                        <div class="language-selector-inline">
                            <label for="recipeLanguageSelect">🌍 Language:</label>
                            <select id="recipeLanguageSelect" onchange="switchRecipeLanguage()">
                                ${languageOptions}
                            </select>
                        </div>
                        <div class="action-buttons">
                            <button onclick="addToWeeklyPlan(${recipe.id})" class="btn btn-primary btn-sm">📅 Add to Plan</button>
                            <button onclick="editRecipe(${recipe.id})" class="btn btn-secondary btn-sm">✏️ Edit</button>
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

                        <div id="substitutionResult" class="substitution-result" style="display: none;"></div>
                    </div>

                    <div class="tab-panel" id="rating-panel" style="display: none;">
                        ${buildRatingSection(recipe)}
                    </div>

                    <div class="tab-panel" id="nutrition-panel" style="display: none;">
                        <h3>Health Score</h3>
                        ${healthScoreHtml}
                    </div>

                    <div class="tab-panel" id="translations-panel" style="display: none;">
                        ${buildTranslationsSection(recipe)}
                    </div>
                </div>
            `;

            modal.style.display = 'flex';
        }
    } catch (error) {
        showError('Error loading recipe: ' + error.message);
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

function buildIngredientsListHtml(recipe, servings) {
    const scale = servings / window.originalServings;
    const ingredients = getIngredientsForLanguage(recipe, window.selectedLanguage);
    const scaledIngredients = scaleIngredients(ingredients, scale);

    let html = '<h3>Ingredients</h3><ul class="ingredients-list">';
    scaledIngredients.forEach(ing => {
        const escapedIng = escapeHtml(ing).replace(/'/g, '&apos;');
        html += `
            <li class="ingredient-item">
                <span class="ingredient-text">${escapeHtml(ing)}</span>
                <button class="btn-substitute" onclick="substituteIngredient('${escapedIng}', ${recipe.id})" title="Find substitutes">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    Substitute
                </button>
            </li>
        `;
    });
    html += '</ul>';
    return html;
}

function buildInstructionsHtml(recipe) {
    const instructions = getInstructionsForLanguage(recipe, window.selectedLanguage);

    let html = '<h3>Instructions</h3>';
    if (instructions && instructions.length > 0) {
        html += '<ol class="instructions-list">';
        instructions.forEach(inst => {
            html += `<li>${escapeHtml(inst)}</li>`;
        });
        html += '</ol>';
    } else {
        html += '<p style="color: var(--text-secondary);">No instructions available</p>';
    }
    return html;
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

async function substituteIngredient(ingredient, recipeId) {
    const resultDiv = document.getElementById('substitutionResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div class="loading">Finding substitutes...</div>';

    try {
        const recipe = window.currentRecipeData;
        const response = await fetch('/api/ingredients/substitute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ingredient: ingredient,
                recipe_context: {
                    title: recipe.title,
                    type: recipe.tags ? recipe.tags.join(', ') : ''
                }
            })
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <div class="substitution-box">
                    <h3>Substitutes for: ${escapeHtml(data.ingredient)}</h3>
                    <div class="substitution-suggestions">
                        ${formatSuggestions(data.suggestions)}
                    </div>
                    <button onclick="closeSubstitution()" class="btn btn-secondary btn-sm" style="margin-top: 1rem;">Close</button>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-error">${escapeHtml(data.message)}</div>`;
            setTimeout(() => resultDiv.style.display = 'none', 3000);
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-error">Error: ${escapeHtml(error.message)}</div>`;
        setTimeout(() => resultDiv.style.display = 'none', 3000);
    }
}

function formatSuggestions(text) {
    // Convert markdown-style numbered list to HTML
    let html = text.replace(/\n/g, '<br>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    return `<div class="suggestion-text">${html}</div>`;
}

function closeSubstitution() {
    document.getElementById('substitutionResult').style.display = 'none';
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
    const shouldTranslate = document.getElementById('translateAfterSave').checked;

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
        language: 'Original'
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

            if (shouldTranslate) {
                // Redirect to translator with pre-filled data
                alert('Recipe saved! Redirecting to translator...');
                // TODO: Add translation functionality
                window.location.reload();
            } else {
                alert('Recipe saved successfully!');
                loadRecipes(); // Reload the recipes list
            }
        } else {
            alert('Error saving recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error saving recipe: ' + error.message);
    }
}
