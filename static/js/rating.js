/**
 * Recipe Rating Component
 * Shared functions for rating recipes
 */

function renderStarRating(rating, showCount = true, count = 0) {
    if (!rating) {
        rating = 0;
    }

    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    let html = '<div class="rating-display">';
    html += '<div class="stars">';

    // Full stars
    for (let i = 0; i < fullStars; i++) {
        html += '<span class="star filled">★</span>';
    }

    // Half star
    if (hasHalfStar) {
        html += '<span class="star half">★</span>';
    }

    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
        html += '<span class="star">★</span>';
    }

    html += '</div>';

    if (showCount && count > 0) {
        html += `<span class="rating-count">(${count})</span>`;
    }

    html += '</div>';
    return html;
}

function renderInteractiveStarRating(currentRating = 0) {
    let html = '<div class="star-rating-input" id="starRatingInput">';

    for (let i = 1; i <= 5; i++) {
        const active = i <= currentRating ? 'active' : '';
        html += `<button type="button" class="star-btn ${active}" data-rating="${i}" onclick="setRating(${i})">★</button>`;
    }

    html += '</div>';
    return html;
}

let currentRatingValue = 0;

function setRating(rating) {
    currentRatingValue = rating;

    // Update visual state
    const stars = document.querySelectorAll('.star-btn');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

async function submitRating(recipeId) {
    const rating = currentRatingValue;
    const notes = document.getElementById('ratingNotes')?.value || '';
    const wouldMakeAgain = document.getElementById('wouldMakeAgain')?.checked ?? true;
    const dateCooked = document.getElementById('dateCooked')?.value || new Date().toISOString().split('T')[0];

    if (rating === 0) {
        alert('Please select a rating (1-5 stars)');
        return;
    }

    try {
        const response = await fetch(`/api/recipes/${recipeId}/rate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: rating,
                notes: notes,
                would_make_again: wouldMakeAgain,
                date_cooked: dateCooked
            })
        });

        const data = await response.json();

        if (data.success) {
            showRatingSuccess('Rating saved successfully!');
            // Reload the recipe to show updated rating
            setTimeout(() => {
                if (typeof loadRecipeDetails === 'function') {
                    loadRecipeDetails(recipeId);
                } else if (typeof loadRecipes === 'function') {
                    loadRecipes();
                }
            }, 1000);
        } else {
            alert('Failed to save rating: ' + data.message);
        }
    } catch (error) {
        alert('Error saving rating: ' + error.message);
    }
}

function showRatingSuccess(message) {
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

function buildRatingSection(recipe) {
    const userRating = recipe.user_rating;
    const averageRating = recipe.average_rating || 0;
    const ratingCount = recipe.rating_count || 0;

    let html = '<div class="rating-section">';

    // Show average rating if any ratings exist
    if (ratingCount > 0) {
        html += '<h3>📊 Average Rating</h3>';
        html += renderStarRating(averageRating, true, ratingCount);
        html += '<hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-color);">';
    }

    // User's rating form
    html += '<h3>⭐ Your Rating</h3>';
    html += '<div class="your-rating">';

    html += '<div class="rating-form-group">';
    html += '<label>Rating</label>';
    html += renderInteractiveStarRating(userRating?.rating || 0);

    if (userRating?.rating) {
        currentRatingValue = userRating.rating;
    }
    html += '</div>';

    html += '<div class="rating-form-group">';
    html += '<label>Cooking Notes</label>';
    html += `<textarea id="ratingNotes" class="rating-notes" placeholder="How did it turn out? Any modifications?">${userRating?.notes || ''}</textarea>`;
    html += '</div>';

    html += '<div class="rating-form-group">';
    html += '<label class="rating-checkbox">';
    html += `<input type="checkbox" id="wouldMakeAgain" ${userRating?.would_make_again !== false ? 'checked' : ''}>`;
    html += '<span>I would make this again</span>';
    html += '</label>';
    html += '</div>';

    html += '<div class="rating-form-group">';
    html += '<label>Date Cooked</label>';
    const today = new Date().toISOString().split('T')[0];
    const dateValue = userRating?.date_cooked || today;
    html += `<input type="date" id="dateCooked" class="rating-date" value="${dateValue}">`;
    html += '</div>';

    html += '<div class="rating-actions">';
    html += `<button onclick="submitRating(${recipe.id})" class="btn btn-primary">Save Rating</button>`;
    html += '</div>';

    html += '</div>'; // your-rating
    html += '</div>'; // rating-section

    return html;
}
