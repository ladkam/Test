// Admin Dashboard JavaScript

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;

        // Update buttons
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Show alert message
function showAlert(message, type = 'success') {
    const alertsContainer = document.getElementById('adminAlerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<strong>${type === 'success' ? 'Success!' : 'Error:'}</strong> ${message}`;

    alertsContainer.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);

    // Scroll to alert
    alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Languages Management
async function addLanguage() {
    const input = document.getElementById('newLanguage');
    const language = input.value.trim();

    if (!language) {
        showAlert('Please enter a language name', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/languages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            input.value = '';
            // Reload page to refresh language list
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to add language: ' + error.message, 'error');
    }
}

async function removeLanguage(language) {
    if (!confirm(`Remove "${language}" from the language list?`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/languages', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to remove language: ' + error.message, 'error');
    }
}

// Prompts Management
async function savePrompts() {
    const translationPrompt = document.getElementById('translationPrompt').value;
    const systemPrompt = document.getElementById('systemPrompt').value;

    if (!translationPrompt || !systemPrompt) {
        showAlert('Both prompts are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                translation_prompt: translationPrompt,
                system_prompt: systemPrompt
            })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to save prompts: ' + error.message, 'error');
    }
}

async function resetSettings() {
    if (!confirm('Reset all settings to defaults? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/admin/settings/reset', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to reset settings: ' + error.message, 'error');
    }
}

// API Settings Management
const MODEL_OPTIONS = {
    mistral: [
        { value: 'open-mistral-nemo', label: 'Open Mistral Nemo (Free)', free: true },
        { value: 'mistral-small-latest', label: 'Mistral Small Latest', free: false },
        { value: 'mistral-medium-latest', label: 'Mistral Medium Latest', free: false },
        { value: 'mistral-large-latest', label: 'Mistral Large Latest', free: false },
        { value: 'open-mixtral-8x7b', label: 'Open Mixtral 8x7B (Free)', free: true },
        { value: 'open-mixtral-8x22b', label: 'Open Mixtral 8x22B (Free)', free: true }
    ],
    groq: [
        { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile (Recommended)', free: true },
        { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant (Ultra Fast)', free: true },
        { value: 'openai/gpt-oss-120b', label: 'GPT OSS 120B (Highest Quality)', free: true },
        { value: 'openai/gpt-oss-20b', label: 'GPT OSS 20B (Fast)', free: true }
    ]
};

function updateModelOptions() {
    const provider = document.getElementById('aiProvider').value;
    const modelSelect = document.getElementById('aiModel');
    const modelHelp = document.getElementById('modelHelp');
    const currentModel = modelSelect.value;

    // Clear existing options
    modelSelect.innerHTML = '';

    // Add options for the selected provider
    const options = MODEL_OPTIONS[provider];
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.label;
        modelSelect.appendChild(optionElement);
    });

    // Try to keep the same model if it exists in the new provider
    if (currentModel && Array.from(modelSelect.options).some(opt => opt.value === currentModel)) {
        modelSelect.value = currentModel;
    }

    // Update help text
    if (provider === 'mistral') {
        modelHelp.textContent = 'Mistral AI models. Free tier: open-mistral-nemo, open-mixtral-8x7b, open-mixtral-8x22b';
    } else {
        modelHelp.textContent = 'Groq models (All free with generous limits). Llama 3.3 70B Versatile recommended for best quality.';
    }
}

async function saveApiSettings() {
    const groqApiKey = document.getElementById('groqApiKey').value.trim();
    const mistralApiKey = document.getElementById('mistralApiKey').value.trim();
    const aiProvider = document.getElementById('aiProvider').value;
    const aiModel = document.getElementById('aiModel').value;
    const nytCookie = document.getElementById('nytCookie').value.trim();

    try {
        const response = await fetch('/api/admin/api-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                groq_api_key: groqApiKey,
                mistral_api_key: mistralApiKey,
                ai_provider: aiProvider,
                ai_model: aiModel,
                nyt_cookie: nytCookie
            })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to save API settings: ' + error.message, 'error');
    }
}

// User Management
async function createUser() {
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value.trim();
    const role = document.getElementById('newRole').value;

    if (!username || !password) {
        showAlert('Username and password are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/users/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to create user: ' + error.message, 'error');
    }
}

async function deleteUser(userId, username) {
    if (!confirm(`Delete user "${username}"? This cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/users/${userId}/delete`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to delete user: ' + error.message, 'error');
    }
}

// Password Change
let currentUserId = null;

function showChangePassword(userId, username) {
    currentUserId = userId;
    document.getElementById('changePasswordUsername').textContent = username;
    document.getElementById('newUserPassword').value = '';
    document.getElementById('confirmUserPassword').value = '';
    document.getElementById('changePasswordModal').style.display = 'flex';
}

function closeChangePassword() {
    document.getElementById('changePasswordModal').style.display = 'none';
    currentUserId = null;
}

async function changePassword() {
    const newPassword = document.getElementById('newUserPassword').value.trim();
    const confirmPassword = document.getElementById('confirmUserPassword').value.trim();

    if (!newPassword || !confirmPassword) {
        showAlert('Both password fields are required', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/admin/users/${currentUserId}/password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message, 'success');
            closeChangePassword();
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('Failed to change password: ' + error.message, 'error');
    }
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('changePasswordModal');
    if (e.target === modal) {
        closeChangePassword();
    }
});

// Enter key handler for language input
document.getElementById('newLanguage')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        addLanguage();
    }
});

// Initialize model options on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the admin page with API settings
    if (document.getElementById('aiProvider') && document.getElementById('aiModel')) {
        updateModelOptions();

        // Set the current model after options are populated
        if (window.currentAiModel) {
            document.getElementById('aiModel').value = window.currentAiModel;
        }
    }
});
