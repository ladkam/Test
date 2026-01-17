/**
 * Unified Import Page - NYT Translator + Photo OCR
 */

let currentImageData = null;

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabs = document.querySelectorAll('.import-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });

    // NYT Form submission
    const form = document.getElementById('recipeForm');
    form.addEventListener('submit', handleNYTSubmit);

    // Photo upload
    const uploadArea = document.getElementById('uploadArea');
    const photoInput = document.getElementById('photoInput');

    uploadArea.addEventListener('click', () => {
        if (!currentImageData) {
            photoInput.click();
        }
    });

    photoInput.addEventListener('change', handleFileSelect);

    // Change image button
    document.getElementById('changeImageBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        resetPhotoUpload();
    });

    // Process image button
    document.getElementById('processImage')?.addEventListener('click', processImage);

    // Review form
    document.getElementById('reviewForm').addEventListener('submit', saveExtractedRecipe);
    document.getElementById('cancelReview').addEventListener('click', () => {
        document.getElementById('reviewModal').style.display = 'none';
    });

    // Modal close
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('reviewModal').style.display = 'none';
    });

    // Save to library button (for NYT results)
    // This will be dynamically added when results are shown
});

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.import-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.import-tab[data-tab="${tabName}"]`).classList.add('active');

    // Update sections
    document.querySelectorAll('.import-section').forEach(s => s.style.display = 'none');
    document.getElementById(`${tabName}-import`).style.display = 'block';
}

// ============= NYT Import Functions =============

async function handleNYTSubmit(e) {
    e.preventDefault();

    const url = document.getElementById('recipeUrl').value.trim();
    const language = document.getElementById('language').value;
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');

    // Reset previous results
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    // Show loading state
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';

    try {
        const response = await fetch('/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, language })
        });

        const data = await response.json();

        if (data.success) {
            displayNYTResults(data.recipe);
        } else {
            showError(data.message || 'Failed to translate recipe');
        }
    } catch (error) {
        showError('Error: ' + error.message);
    } finally {
        // Reset button
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

function displayNYTResults(recipe) {
    const resultsDiv = document.getElementById('results');
    const titleEl = document.getElementById('recipeTitle');
    const contentEl = document.getElementById('recipeContent');
    const imageContainer = document.getElementById('recipeImageContainer');
    const imageEl = document.getElementById('recipeImage');

    // Set title
    titleEl.textContent = recipe.title || 'Recipe';

    // Set image
    if (recipe.image) {
        imageEl.src = recipe.image;
        imageContainer.style.display = 'block';
    } else {
        imageContainer.style.display = 'none';
    }

    // Set content
    contentEl.innerHTML = formatMarkdown(recipe.content || '');

    // Add Save to Library button if not exists
    let saveBtn = document.getElementById('saveToLibraryBtn');
    if (!saveBtn) {
        saveBtn = document.createElement('button');
        saveBtn.id = 'saveToLibraryBtn';
        saveBtn.className = 'btn btn-primary';
        saveBtn.textContent = 'Save to Library';
        document.querySelector('.results-actions').appendChild(saveBtn);
    }

    saveBtn.onclick = () => saveNYTToLibrary(recipe);

    // Show results
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function saveNYTToLibrary(recipe) {
    const saveBtn = document.getElementById('saveToLibraryBtn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        const response = await fetch('/api/recipes/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ recipeData: recipe })
        });

        const data = await response.json();

        if (data.success) {
            saveBtn.innerHTML = '✓ Saved!';
            setTimeout(() => {
                window.location.href = '/library';
            }, 1000);
        } else {
            alert('Error saving recipe: ' + (data.message || 'Unknown error'));
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }
    } catch (error) {
        alert('Error saving recipe: ' + error.message);
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    }
}

// ============= Photo OCR Functions =============

function resetPhotoUpload() {
    currentImageData = null;
    document.getElementById('photoInput').value = '';
    document.querySelector('.upload-prompt').style.display = 'block';
    document.getElementById('imagePreview').style.display = 'none';
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
        currentImageData = e.target.result;

        // Show preview
        document.getElementById('previewImage').src = currentImageData;
        document.querySelector('.upload-prompt').style.display = 'none';
        document.getElementById('imagePreview').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

async function processImage() {
    if (!currentImageData) return;

    const uploadArea = document.getElementById('uploadArea');
    const processingStatus = document.getElementById('processingStatus');
    const processBtn = document.getElementById('processImage');

    // Show processing UI
    uploadArea.style.display = 'none';
    processingStatus.style.display = 'block';
    processBtn.disabled = true;

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
            // Open review modal with extracted data
            openReviewModal(data.recipe);
            resetPhotoUpload();
        } else {
            alert('Error extracting recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error processing image: ' + error.message);
    } finally {
        // Reset UI
        uploadArea.style.display = 'block';
        processingStatus.style.display = 'none';
        processBtn.disabled = false;
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
            document.getElementById('reviewModal').style.display = 'none';

            if (shouldTranslate) {
                alert('Recipe saved! Redirecting to translator...');
                // TODO: Add translation functionality
                window.location.href = '/library';
            } else {
                alert('Recipe saved successfully!');
                window.location.href = '/library';
            }
        } else {
            alert('Error saving recipe: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error saving recipe: ' + error.message);
    }
}

// ============= Utility Functions =============

function formatMarkdown(markdown) {
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

    // Wrap consecutive list items
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

function showError(message) {
    const errorDiv = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
