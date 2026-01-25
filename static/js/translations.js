/**
 * Recipe Translation Management
 */

const SUPPORTED_LANGUAGES = {
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

function buildTranslationsSection(recipe) {
    const existingTranslations = recipe.translations || {};
    const availableLanguages = Object.keys(SUPPORTED_LANGUAGES).filter(
        code => !existingTranslations[code]
    );

    let html = '<div class="translations-section">';
    html += '<h3>🌍 Manage Translations</h3>';

    // Show existing translations
    if (Object.keys(existingTranslations).length > 0) {
        html += '<div class="existing-translations">';
        html += '<h4 style="font-size: 0.9375rem; margin-bottom: 0.75rem; color: var(--text-secondary);">Existing Translations</h4>';
        html += '<div class="translation-list">';

        Object.keys(existingTranslations).forEach(langCode => {
            const translation = existingTranslations[langCode];
            html += `
                <div class="translation-item">
                    <div class="translation-info">
                        <span class="translation-flag">${SUPPORTED_LANGUAGES[langCode]}</span>
                        <span class="translation-title">${escapeHtml(translation.title || '')}</span>
                    </div>
                    <button onclick="deleteTranslation(${recipe.id}, '${langCode}')" class="btn-delete-translation" title="Delete translation">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M2 4h12M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1m2 0v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h10z" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                    </button>
                </div>
            `;
        });

        html += '</div></div>';
    }

    // Add new translation
    if (availableLanguages.length > 0) {
        html += '<div class="add-translation">';
        html += '<h4 style="font-size: 0.9375rem; margin-bottom: 0.75rem; margin-top: 1.5rem; color: var(--text-secondary);">Add New Translation</h4>';
        html += '<div class="translation-form">';
        html += '<select id="translationLanguage" class="translation-language-select">';
        html += '<option value="">Select language...</option>';

        availableLanguages.forEach(code => {
            html += `<option value="${code}">${SUPPORTED_LANGUAGES[code]}</option>`;
        });

        html += '</select>';
        html += `<button onclick="addTranslation(${recipe.id})" class="btn btn-primary btn-sm">Translate</button>`;
        html += '</div>';
        html += '</div>';
    } else {
        html += '<p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 1rem;">All supported languages have been translated!</p>';
    }

    html += '</div>';
    return html;
}

async function addTranslation(recipeId) {
    const languageCode = document.getElementById('translationLanguage').value;

    if (!languageCode) {
        alert('Please select a language');
        return;
    }

    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Translating...';
    button.disabled = true;

    try {
        const response = await fetch(`/api/recipes/${recipeId}/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language_code: languageCode })
        });

        const data = await response.json();

        if (data.success) {
            showTranslationSuccess(`Successfully translated to ${SUPPORTED_LANGUAGES[languageCode]}!`);
            // Reload recipe to show new translation
            setTimeout(() => {
                if (typeof loadRecipeDetails === 'function') {
                    loadRecipeDetails(recipeId);
                } else if (typeof showRecipeDetail === 'function') {
                    showRecipeDetail(recipeId);
                }
            }, 1000);
        } else {
            alert('Translation failed: ' + data.message);
            button.textContent = originalText;
            button.disabled = false;
        }
    } catch (error) {
        alert('Error: ' + error.message);
        button.textContent = originalText;
        button.disabled = false;
    }
}

async function deleteTranslation(recipeId, languageCode) {
    if (!confirm(`Delete ${SUPPORTED_LANGUAGES[languageCode]} translation?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/recipes/${recipeId}/translations/${languageCode}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showTranslationSuccess('Translation deleted');
            // Reload recipe
            setTimeout(() => {
                if (typeof loadRecipeDetails === 'function') {
                    loadRecipeDetails(recipeId);
                } else if (typeof showRecipeDetail === 'function') {
                    showRecipeDetail(recipeId);
                }
            }, 500);
        } else {
            alert('Failed to delete: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function showTranslationSuccess(message) {
    const toast = document.createElement('div');
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
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
