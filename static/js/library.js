/**
 * Recipe Library functionality
 */

let allRecipes = [];
let filteredRecipes = [];

// Current image data for OCR
let currentImageData = null;

// Load recipes on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();

    // Search input
    document.getElementById('searchInput').addEventListener('input', filterRecipes);

    // Duration filter
    document.getElementById('durationFilter').addEventListener('change', filterRecipes);

    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', clearFilters);

    // Upload photo button
    document.getElementById('uploadPhotoBtn').addEventListener('click', openUploadModal);

    // Photo input
    document.getElementById('photoInput').addEventListener('change', handleFileSelect);

    // Upload area click
    document.getElementById('uploadArea').addEventListener('click', () => {
        if (!currentImageData) {
            document.getElementById('photoInput').click();
        }
    });

    // Change image button
    document.getElementById('changeImageBtn').addEventListener('click', (e) => {
        e.stopPropagation();
        currentImageData = null;
        document.getElementById('photoInput').value = '';
        document.getElementById('uploadPrompt').style.display = 'block';
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('processImage').disabled = true;
    });

    // Process image button
    document.getElementById('processImage').addEventListener('click', processImage);

    // Cancel upload
    document.getElementById('cancelUpload').addEventListener('click', closeUploadModal);

    // Review form
    document.getElementById('reviewForm').addEventListener('submit', saveExtractedRecipe);

    // Cancel review
    document.getElementById('cancelReview').addEventListener('click', closeReviewModal);

    // Modal close buttons
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
            recipe.title_translated?.toLowerCase().includes(searchTerm) ||
            recipe.title_original?.toLowerCase().includes(searchTerm) ||
            (recipe.ingredients_translated || []).some(ing => ing.toLowerCase().includes(searchTerm));

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
    const title = recipe.title_translated || recipe.title_original;
    const time = formatTime(recipe.total_time);

    return `
        <div class="recipe-card" data-recipe-id="${recipe.id}">
            <div class="card-clickable">
                ${imageUrl ? `<img src="${imageUrl}" alt="${title}" class="recipe-card-image">` : '<div class="recipe-card-image-placeholder">No Image</div>'}
                <div class="recipe-card-content">
                    <h3 class="recipe-card-title">${escapeHtml(title)}</h3>
                    ${time ? `<p class="recipe-card-time">⏱️ ${time}</p>` : ''}
                    ${recipe.language ? `<span class="recipe-card-lang">${escapeHtml(recipe.language)}</span>` : ''}
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

function formatTime(minutes) {
    if (!minutes) return '';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

async function showRecipeDetail(recipeId) {
    try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        const data = await response.json();

        if (data.success) {
            const recipe = data.recipe;
            const modal = document.getElementById('recipeModal');
            const content = document.getElementById('modalContent');

            // Build ingredients section with substitution buttons
            let ingredientsHtml = '';
            if (recipe.ingredients_translated && recipe.ingredients_translated.length > 0) {
                ingredientsHtml = '<div class="ingredients-section"><h3>Ingredients</h3><ul class="ingredients-list">';
                recipe.ingredients_translated.forEach((ing, idx) => {
                    ingredientsHtml += `
                        <li class="ingredient-item">
                            <span class="ingredient-text">${escapeHtml(ing)}</span>
                            <button class="btn-substitute" onclick="substituteIngredient('${escapeHtml(ing)}', ${recipe.id})" title="Find substitutes">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                                Substitute
                            </button>
                        </li>
                    `;
                });
                ingredientsHtml += '</ul></div>';
            }

            content.innerHTML = `
                <div class="recipe-detail">
                    ${recipe.image_url ? `<img src="${recipe.image_url}" class="recipe-detail-image" alt="${recipe.title_translated}">` : ''}
                    <h2>${escapeHtml(recipe.title_translated || recipe.title_original)}</h2>

                    <div class="recipe-detail-meta">
                        ${recipe.total_time ? `<span>⏱️ ${formatTime(recipe.total_time)}</span>` : ''}
                        ${recipe.servings ? `<span>🍽️ ${escapeHtml(recipe.servings)}</span>` : ''}
                        ${recipe.language ? `<span>🌍 ${escapeHtml(recipe.language)}</span>` : ''}
                    </div>

                    <div class="recipe-detail-actions">
                        <button onclick="editRecipe(${recipe.id})" class="btn btn-secondary">Edit Recipe</button>
                        <button onclick="addToWeeklyPlan(${recipe.id})" class="btn btn-primary">Add to Weekly Plan</button>
                    </div>

                    ${ingredientsHtml}

                    <div class="recipe-detail-content">
                        <div class="recipe-tabs">
                            <button class="recipe-tab active" data-lang="translated">Translated</button>
                            <button class="recipe-tab" data-lang="original">Original</button>
                        </div>

                        <div class="recipe-tab-content active" id="translated-content">
                            ${formatRecipeContent(recipe.content_translated || 'No translation available')}
                        </div>

                        <div class="recipe-tab-content" id="original-content" style="display: none;">
                            ${formatRecipeContent(recipe.content_original)}
                        </div>
                    </div>

                    <div id="substitutionResult" class="substitution-result" style="display: none;"></div>
                </div>
            `;

            // Store recipe data for substitutions
            window.currentRecipeData = recipe;

            // Tab switching
            content.querySelectorAll('.recipe-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    const lang = tab.dataset.lang;
                    content.querySelectorAll('.recipe-tab').forEach(t => t.classList.remove('active'));
                    content.querySelectorAll('.recipe-tab-content').forEach(c => c.style.display = 'none');
                    tab.classList.add('active');
                    document.getElementById(`${lang}-content`).style.display = 'block';
                });
            });

            modal.style.display = 'flex';
        }
    } catch (error) {
        showError('Error loading recipe: ' + error.message);
    }
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

function addToWeeklyPlan(recipeId) {
    window.location.href = `/planner?add=${recipeId}`;
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
                    title: recipe.title_translated || recipe.title_original,
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
