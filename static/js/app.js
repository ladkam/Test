// Recipe Translator App JavaScript

// DOM elements - URL form
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

// DOM elements - OCR form
const ocrForm = document.getElementById('ocrForm');
const imageUploadArea = document.getElementById('imageUploadArea');
const recipeImageInput = document.getElementById('recipeImage');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const removeImageBtn = document.getElementById('removeImage');
const ocrSubmitBtn = document.getElementById('ocrSubmitBtn');
const ocrResults = document.getElementById('ocrResults');
const ocrText = document.getElementById('ocrText');
const detectedLang = document.getElementById('detectedLang');
const ocrConfidence = document.getElementById('ocrConfidence');
const translateOcrBtn = document.getElementById('translateOcrBtn');

// DOM elements - Tabs
const inputTabs = document.querySelectorAll('.input-tab');
const tabContents = document.querySelectorAll('.tab-content');

// Store the current recipe data
let currentRecipe = null;
let currentOcrData = null;

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
        // Call API (always convert to metric and translate)
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                language,
                convert_units: true,
                translate: true
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

// ==========================================
// Tab Switching Logic
// ==========================================

inputTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;

        // Update active tab
        inputTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show corresponding content
        tabContents.forEach(content => {
            if (content.dataset.tab === targetTab) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });

        // Clear errors when switching tabs
        errorSection.style.display = 'none';
    });
});

// ==========================================
// Image Upload Handling
// ==========================================

// Handle file selection
recipeImageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleImageFile(file);
    }
});

// Handle drag and drop
imageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    imageUploadArea.classList.add('drag-over');
});

imageUploadArea.addEventListener('dragleave', () => {
    imageUploadArea.classList.remove('drag-over');
});

imageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUploadArea.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        // Update the file input
        const dt = new DataTransfer();
        dt.items.add(file);
        recipeImageInput.files = dt.files;
        handleImageFile(file);
    } else {
        showError('Please drop a valid image file');
    }
});

function handleImageFile(file) {
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please use PNG, JPG, GIF, or WebP images.');
        return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        imagePreview.style.display = 'block';
        document.querySelector('.upload-placeholder').style.display = 'none';
    };
    reader.readAsDataURL(file);

    // Reset OCR results
    ocrResults.style.display = 'none';
    currentOcrData = null;
}

// Handle remove image
removeImageBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    recipeImageInput.value = '';
    imagePreview.style.display = 'none';
    document.querySelector('.upload-placeholder').style.display = 'flex';
    ocrResults.style.display = 'none';
    currentOcrData = null;
});

// ==========================================
// OCR Form Submission
// ==========================================

function setOcrLoading(isLoading, btn) {
    btn.disabled = isLoading;
    const btnTextEl = btn.querySelector('.btn-text');
    const btnLoaderEl = btn.querySelector('.btn-loader');

    if (isLoading) {
        btnTextEl.style.display = 'none';
        btnLoaderEl.style.display = 'flex';
    } else {
        btnTextEl.style.display = 'block';
        btnLoaderEl.style.display = 'none';
    }
}

ocrForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Clear previous errors
    errorSection.style.display = 'none';

    // Validate image
    const file = recipeImageInput.files[0];
    if (!file) {
        showError('Please select a recipe image');
        return;
    }

    setOcrLoading(true, ocrSubmitBtn);

    try {
        // Create form data
        const formData = new FormData();
        formData.append('image', file);

        // Call OCR API
        const response = await fetch('/api/ocr', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'OCR processing failed');
        }

        // Store OCR data
        currentOcrData = {
            text: data.text,
            detected_language: data.detected_language,
            confidence: data.confidence,
            image_url: data.image_url
        };

        // Update OCR results UI
        ocrText.value = data.text;
        detectedLang.textContent = data.detected_language;
        ocrConfidence.textContent = `${data.confidence}%`;
        ocrResults.style.display = 'block';

        // Scroll to results
        ocrResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    } catch (error) {
        showError(error.message);
    } finally {
        setOcrLoading(false, ocrSubmitBtn);
    }
});

// ==========================================
// OCR Translation
// ==========================================

translateOcrBtn.addEventListener('click', async () => {
    if (!currentOcrData) {
        showError('No OCR data available. Please extract text first.');
        return;
    }

    // Get the possibly edited text from textarea
    const text = ocrText.value.trim();
    if (!text) {
        showError('No text to translate');
        return;
    }

    const targetLanguage = document.getElementById('ocrLanguage').value;

    setOcrLoading(true, translateOcrBtn);

    try {
        const response = await fetch('/api/ocr/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                source_language: currentOcrData.detected_language,
                target_language: targetLanguage,
                image_url: currentOcrData.image_url
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Translation failed');
        }

        // Redirect to results page
        if (data.redirect) {
            window.location.href = data.redirect;
        }

    } catch (error) {
        showError(error.message);
    } finally {
        setOcrLoading(false, translateOcrBtn);
    }
});
