/**
 * Shared Utility Functions
 * Used across multiple pages in the Recipe Translator app
 */

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

// ---------------------------------------------------------------------------
// Servings scaling, shared by the library, planner and help pages.
//
// Scales the amounts of an ingredient line ("1½ cucharadas", "450 to 680 g",
// "1 1/2 cups") but leaves alone the things that must not change with servings:
// package sizes in parentheses ("1 (400 g) can"), cut/pan sizes (cm, mm, inch)
// and temperatures (°C/°F).
// ---------------------------------------------------------------------------
const UNICODE_FRACTIONS = {
    '½': 1 / 2, '¼': 1 / 4, '¾': 3 / 4, '⅓': 1 / 3, '⅔': 2 / 3,
    '⅛': 1 / 8, '⅜': 3 / 8, '⅝': 5 / 8, '⅞': 7 / 8,
    '⅕': 1 / 5, '⅖': 2 / 5, '⅗': 3 / 5, '⅘': 4 / 5, '⅙': 1 / 6, '⅚': 5 / 6
};
const _FR = Object.keys(UNICODE_FRACTIONS).join('');
const _QTY_RE = new RegExp(
    '(\\d+\\s+\\d+\\/\\d+|\\d+\\/\\d+|\\d+\\s?[' + _FR + ']|\\d+(?:[.,]\\d+)?|[' + _FR + '])' +
    '(?=(\\s*-?\\s*(?:cm|mm|centím|inch|pulgada|pouce|°|º|degree|grado|degré|%))?)',
    'g'
);

function parseQuantity(str) {
    let s = str.trim().replace(',', '.');
    let total = 0;
    for (const [ch, val] of Object.entries(UNICODE_FRACTIONS)) {
        if (s.includes(ch)) { total += val; s = s.replace(ch, ''); }
    }
    for (const part of s.trim().split(/\s+/).filter(Boolean)) {
        if (part.includes('/')) {
            const [n, d] = part.split('/').map(Number);
            total += n / d;
        } else {
            total += parseFloat(part);
        }
    }
    return total;
}

function formatQuantity(value, isMetricAmount) {
    if (isMetricAmount) {
        // grams / ml: print like a metric recipe would
        if (value >= 250) return String(Math.round(value / 10) * 10);
        if (value >= 50) return String(Math.round(value / 5) * 5);
        if (value >= 10) return String(Math.round(value));
        return String(parseFloat(value.toFixed(1)));
    }
    const whole = Math.floor(value + 1e-9);
    const frac = value - whole;
    const nice = [[0, ''], [1 / 4, '¼'], [1 / 3, '⅓'], [1 / 2, '½'], [2 / 3, '⅔'], [3 / 4, '¾'], [1, '']];
    let best = nice[0];
    for (const candidate of nice) {
        if (Math.abs(frac - candidate[0]) < Math.abs(frac - best[0])) best = candidate;
    }
    if (Math.abs(frac - best[0]) <= 0.04) {
        const w = best[0] === 1 ? whole + 1 : whole;
        if (!best[1]) return String(w);
        return w > 0 ? `${w}${best[1]}` : best[1];
    }
    return String(parseFloat(value.toFixed(2)));
}

function scaleIngredientLine(line, scale) {
    if (!line || typeof line !== 'string' || scale === 1) return line;
    let depth = 0;
    let out = '';
    let last = 0;
    _QTY_RE.lastIndex = 0;
    let match;
    while ((match = _QTY_RE.exec(line)) !== null) {
        // Track parentheses between the previous match and this one.
        for (const ch of line.slice(last, match.index)) {
            if (ch === '(') depth++;
            else if (ch === ')') depth = Math.max(0, depth - 1);
        }
        out += line.slice(last, match.index);
        last = match.index + match[0].length;
        const isSize = Boolean(match[2]);
        const prevChar = match.index > 0 ? line[match.index - 1] : '';
        if (depth > 0 || isSize || /[\w.]/.test(prevChar)) {
            out += match[0];
            continue;
        }
        const after = line.slice(last);
        const isMetricAmount = /^\s*(?:g|kg|ml|l|gr)\b/i.test(after);
        const scaled = parseQuantity(match[1]) * scale;
        const text = formatQuantity(scaled, isMetricAmount);
        out += text;
    }
    return out + line.slice(last);
}

function scaleIngredients(ingredients, scale) {
    if (!Array.isArray(ingredients) || scale === 1) return ingredients;
    return ingredients.map(ing => scaleIngredientLine(ing, scale));
}
