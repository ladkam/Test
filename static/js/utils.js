/**
 * Shared Utility Functions
 * Used across multiple pages in the Recipe Translator app
 */

/**
 * Convert imperial measurements to metric
 * Handles cups, tablespoons, teaspoons, ounces, pounds, and Fahrenheit
 * @param {string} text - Text containing imperial measurements
 * @returns {string} Text with measurements converted to metric
 */
function convertToMetric(text) {
    if (!text) return text;

    let converted = text;

    // Cup conversions (1 cup = 240ml)
    converted = converted.replace(/(\d+\.?\d*)\s*cups?\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 240);
        return `${ml}ml `;
    });

    // Tablespoon conversions (1 tbsp = 15ml)
    converted = converted.replace(/(\d+\.?\d*)\s*(tbsp?|tablespoons?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 15);
        return `${ml}ml `;
    });

    // Teaspoon conversions (1 tsp = 5ml)
    converted = converted.replace(/(\d+\.?\d*)\s*(tsp?|teaspoons?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 5);
        return `${ml}ml `;
    });

    // Ounce (fluid) conversions (1 fl oz = 30ml)
    converted = converted.replace(/(\d+\.?\d*)\s*(fl\.?\s*oz|fluid ounces?)\s+/gi, (match, amount) => {
        const ml = Math.round(parseFloat(amount) * 30);
        return `${ml}ml `;
    });

    // Ounce (weight) conversions (1 oz = 28g)
    converted = converted.replace(/(\d+\.?\d*)\s*oz\s+/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 28);
        return `${g}g `;
    });

    // Pound conversions (1 lb = 454g)
    converted = converted.replace(/(\d+\.?\d*)\s*(lbs?|pounds?)\s+/gi, (match, amount) => {
        const g = Math.round(parseFloat(amount) * 454);
        // Convert to kg if >= 1000g
        if (g >= 1000) {
            return `${(g / 1000).toFixed(1)}kg `;
        }
        return `${g}g `;
    });

    // Fahrenheit to Celsius (for temperatures)
    converted = converted.replace(/(\d+)\s*°?\s*F\b/gi, (match, temp) => {
        const celsius = Math.round((parseFloat(temp) - 32) * 5 / 9);
        return `${celsius}°C`;
    });

    return converted;
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text safe for HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
