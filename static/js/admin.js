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
async function saveApiSettings() {
    const aiModel = document.getElementById('aiModel').value;
    const nytCookie = document.getElementById('nytCookie').value.trim();

    try {
        const response = await fetch('/api/admin/api-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
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
