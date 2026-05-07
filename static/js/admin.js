// Admin Dashboard JavaScript

function showAlert(message, type = 'success') {
    const alertsContainer = document.getElementById('adminAlerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<strong>${type === 'success' ? 'Success!' : 'Error:'}</strong> ${message}`;

    alertsContainer.appendChild(alert);

    setTimeout(() => alert.remove(), 5000);
    alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// User Management
async function createUser() {
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value.trim();

    if (!username || !password) {
        showAlert('Username and password are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/users/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
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
