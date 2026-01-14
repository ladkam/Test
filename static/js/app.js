// Recipe Translator App JavaScript

// DOM elements
const recipeForm = document.getElementById('recipeForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoader = submitBtn.querySelector('.btn-loader');
const resultsSection = document.getElementById('results');
const recipeTitle = document.getElementById('recipeTitle');
const recipeContent = document.getElementById('recipeContent');
const recipeImage = document.getElementById('recipeImage');
const recipeImageContainer = document.getElementById('recipeImageContainer');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const errorSection = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const successSection = document.getElementById('success');
const cookieHelp = document.getElementById('cookieHelp');
const cookieModal = document.getElementById('cookieModal');
const closeModal = document.querySelector('.close');

// Store the current recipe data
let currentRecipe = null;

// Show/hide loading state
function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
    } else {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    successSection.style.display = 'none';
    resultsSection.style.display = 'none';

    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Auto-hide after 10 seconds
    setTimeout(() => {
        errorSection.style.display = 'none';
    }, 10000);
}

// Show success message
function showSuccess() {
    successSection.style.display = 'block';
    errorSection.style.display = 'none';

    // Auto-hide after 3 seconds
    setTimeout(() => {
        successSection.style.display = 'none';
    }, 3000);
}

// Convert markdown to HTML (basic conversion)
function markdownToHtml(markdown) {
    let html = markdown;

    // Headers
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Lists - unordered
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Lists - ordered (already numbered in the content)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    // Wrap consecutive <li> tags in <ol> if they're not already in <ul>
    const lines = html.split('\n');
    let inOrderedList = false;
    let result = [];

    for (let line of lines) {
        if (line.match(/^<li>/) && !inOrderedList && !line.includes('<ul>')) {
            result.push('<ol>');
            inOrderedList = true;
        } else if (inOrderedList && !line.match(/^<li>/)) {
            result.push('</ol>');
            inOrderedList = false;
        }
        result.push(line);
    }

    if (inOrderedList) {
        result.push('</ol>');
    }

    html = result.join('\n');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(\s*<[huo])/g, '$1');
    html = html.replace(/(<\/[huo][^>]*>)\s*<\/p>/g, '$1');

    return html;
}

// Handle form submission
recipeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Clear previous results
    errorSection.style.display = 'none';
    successSection.style.display = 'none';
    resultsSection.style.display = 'none';

    // Get form values
    const url = document.getElementById('recipeUrl').value.trim();
    const language = document.getElementById('language').value;
    const nytCookie = document.getElementById('nytCookie').value.trim();
    const convertUnits = document.getElementById('convertUnits').checked;
    const translate = document.getElementById('translate').checked;

    // Validate
    if (!url) {
        showError('Please enter a recipe URL');
        return;
    }

    if (!url.includes('cooking.nytimes.com')) {
        showError('Please enter a valid NYT Cooking URL');
        return;
    }

    // Set loading state
    setLoading(true);

    try {
        // Call API
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                language,
                nyt_cookie: nytCookie || null,
                convert_units: convertUnits,
                translate: translate
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to translate recipe');
        }

        // Redirect to results page
        if (data.redirect) {
            window.location.href = data.redirect;
        }

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

// Handle copy to clipboard
copyBtn.addEventListener('click', async () => {
    if (!currentRecipe) {
        showError('No recipe to copy');
        return;
    }

    try {
        await navigator.clipboard.writeText(currentRecipe.content);

        // Show visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✓ Copied!';
        copyBtn.classList.add('btn-success');

        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove('btn-success');
        }, 2000);
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = currentRecipe.content;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
            copyBtn.innerHTML = '✓ Copied!';
            copyBtn.classList.add('btn-success');
            setTimeout(() => {
                copyBtn.innerHTML = '📋 Copy';
                copyBtn.classList.remove('btn-success');
            }, 2000);
        } catch (err) {
            showError('Failed to copy recipe: ' + err.message);
        }

        document.body.removeChild(textArea);
    }
});

// Handle download
downloadBtn.addEventListener('click', async () => {
    if (!currentRecipe) {
        showError('No recipe to download');
        return;
    }

    try {
        // Create filename from title
        const filename = currentRecipe.title
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '_')
            .substring(0, 50);

        // Call download API
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: currentRecipe.content,
                filename: filename
            })
        });

        if (!response.ok) {
            throw new Error('Failed to download recipe');
        }

        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename + '.md';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        showError(error.message);
    }
});

// Cookie help modal
cookieHelp.addEventListener('click', (e) => {
    e.preventDefault();
    cookieModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
    cookieModal.style.display = 'none';
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === cookieModal) {
        cookieModal.style.display = 'none';
    }
});

// Auto-update translate checkbox when language is English
document.getElementById('language').addEventListener('change', (e) => {
    const translateCheckbox = document.getElementById('translate');
    if (e.target.value === 'English') {
        translateCheckbox.checked = false;
    } else {
        translateCheckbox.checked = true;
    }
});
