"""
Unit conversion module for converting US/imperial cooking measurements to metric.

Built around how NYT Cooking (and other US sites) actually write recipes:

* quantities: ``2``, ``1.5``, ``1/2``, ``1 1/2``, ``1½``, ``1 ½``, ``½``, ``1⁄2``
* ranges: ``1 to 1½ pounds``, ``2-3 cups``, ``120 to 125 degrees``
* dual units: ``1 cup/240 milliliters``, ``4 ounces (115 grams)`` -> keep NYT's metric
* butter sticks: ``1 stick (½ cup) unsalted butter``, ``½ cup (1 stick) butter``
* package sizes: ``1 (14-ounce) can``, ``a 6-ounce bag``
* oven/internal temperatures written without an F: ``Heat oven to 425 degrees``,
  ``a 350-degree oven``, ``425°``
* pan/cut sizes: ``9-by-13-inch baking dish``, ``½-inch pieces``, ``12-inch skillet``

Teaspoons and tablespoons are deliberately left alone: a spoon is a spoon in both
systems and metric recipes (including Spanish/French ones) use them too.

The converter is idempotent (running it on already-converted text changes nothing),
and it also recognises common Spanish/French/Portuguese names for imperial units
so it can be run on AI-translated text as a safety net (``2 tazas`` -> ``480 ml``).
"""
import re
from typing import Optional, Tuple


UNICODE_FRACTIONS = {
    '½': 1 / 2, '¼': 1 / 4, '¾': 3 / 4,
    '⅓': 1 / 3, '⅔': 2 / 3,
    '⅛': 1 / 8, '⅜': 3 / 8, '⅝': 5 / 8, '⅞': 7 / 8,
    '⅕': 1 / 5, '⅖': 2 / 5, '⅗': 3 / 5, '⅘': 4 / 5,
    '⅙': 1 / 6, '⅚': 5 / 6,
}
_FR = ''.join(UNICODE_FRACTIONS)

# A single quantity. Order matters: longest forms first.
NUM = (
    r'(?:\d+\s+\d+/\d+'          # 1 1/2
    r'|\d+/\d+'                  # 1/2
    r'|\d+\s?[' + _FR + r']'     # 1½, 1 ½
    r'|\d+(?:[.,]\d+)?'          # 2, 1.5, 1,5
    r'|[' + _FR + r'])'          # ½
)
# "a"/"an"/"one"/"half a" in running text ("about a pound of shrimp").
# Includes the Spanish/French/Portuguese articles so translated text such as
# "una taza" / "media taza" / "une tasse" is caught by the safety-net pass.
WORD_NUM = r'(?:half\s+an?|media|medio|meia|demi|une?|una?|uma|an?|one)'
# "1 to 2", "1-2", "1- to 2-inch", "2 a 3" (es), "2 à 3" (fr)
RANGE_SEP = r'\s*-?\s*(?:to|or|a|à|-|–|—)\s*'
QTY = r'(?:' + NUM + r'(?:' + RANGE_SEP + NUM + r')?)'

# unit -> (metric unit, factor). Culinary-friendly factors (1 cup = 240 ml,
# the US legal cup, which is what NYT itself uses in its metric columns).
_UNITS = [
    # volume
    (r'fluid\s+ounces?|fl\.?\s*oz\.?|onzas?\s+líquidas?|onces?\s+liquides?', 'ml', 30.0),
    (r'cups?|tazas?|tasses?|xícaras?|xicaras?', 'ml', 240.0),
    (r'pints?|pintas?', 'ml', 473.0),
    (r'quarts?|qts?\.?', 'ml', 946.0),
    (r'gallons?|galones?|galón', 'ml', 3785.0),
    # weight
    (r'ounces?|oz\.?|onzas?|onces?|onças?', 'g', 28.35),
    (r'pounds?|lbs?\.?|libras?|livres?', 'g', 453.6),
]
_UNIT_LOOKUP = [(re.compile(r'^(?:' + p + r')$', re.IGNORECASE), unit, f) for p, unit, f in _UNITS]
UNIT_ALT = '|'.join(p for p, _, _ in _UNITS)

METRIC_ALT = (
    r'milliliters?|millilitres?|ml|mL|liters?|litres?|l|L|'
    r'grams?|gr?|kilograms?|kilos?|kg|centimeters?|centimetres?|cm|mm'
)
SPOON_ALT = r'tablespoons?|teaspoons?|tbsps?\.?|tsps?\.?|sticks?'
DESCRIPTORS = r'heaping|heaped|packed|lightly\s+packed|firmly\s+packed|scant|generous|rounded|level|full|big|small|large'

INCH_ALT = r'inch(?:es)?|pulgadas?|pouces?|polegadas?'
DEGREE_WORD = r'(?:°|º|˚|-?\s*degrees?|\s*grados?|\s*degrés?|\s*graus?)'

STICK_GRAMS = 113.0
_NO_WORD_BEFORE = r'(?<![\w/.,])'
_NO_LETTER_AFTER = r'(?![A-Za-zÀ-ÿ])'


# ---------------------------------------------------------------------------
# number helpers
# ---------------------------------------------------------------------------

def parse_number(s: str) -> float:
    """Parse '1/2', '1 1/2', '1½', '1 ½', '½', '1.5', '1,5', 'a', 'half a'."""
    s = s.strip().lower()
    if re.fullmatch(WORD_NUM, s):
        return 0.5 if s.startswith(('half', 'medi', 'meia', 'demi')) else 1.0
    s = s.replace(',', '.')
    total = 0.0
    for ch, val in UNICODE_FRACTIONS.items():
        if ch in s:
            total += val
            s = s.replace(ch, '')
    s = s.strip()
    if not s:
        return total
    parts = s.split()
    for part in parts:
        if '/' in part:
            n, d = part.split('/')
            total += float(n) / float(d)
        else:
            total += float(part)
    return total


def _split_range(qty: str) -> Tuple[list, list]:
    """Split '1 to 1½' into ([1.0, 1.5], [' to ']). Single values -> ([x], [])."""
    m = re.fullmatch(r'(' + NUM + r')(' + RANGE_SEP + r')(' + NUM + r')', qty.strip())
    if m:
        word = re.search(r'[^\W\d_]+', m.group(2))
        sep = f' {word.group(0)} ' if word else '-'
        return [parse_number(m.group(1)), parse_number(m.group(3))], [sep]
    return [parse_number(qty)], []


def fmt(value: float) -> str:
    """Format a number without a trailing .0."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f'{value:.1f}'.rstrip('0').rstrip('.')


def _round_metric(value: float) -> float:
    """Round grams/ml the way a metric recipe would print them."""
    if value < 10:
        return round(value * 2) / 2 if value >= 2 else round(value, 1)
    if value < 50:
        return round(value)
    if value < 250:
        return round(value / 5) * 5
    return round(value / 10) * 10


def _metric_values(values: list, base_unit: str, factor: float) -> Tuple[list, str]:
    """Convert a list of values (a range shares one unit) to nicely rounded metric."""
    raw = [v * factor for v in values]
    if max(raw) >= 1000:
        big = 'l' if base_unit == 'ml' else 'kg'
        return [round(v / 1000, 2 if v < 2000 else 1) for v in raw], big
    return [_round_metric(v) for v in raw], base_unit


def _join(values: list, seps: list, unit: str) -> str:
    out = fmt(values[0])
    for sep, v in zip(seps, values[1:]):
        out += sep + fmt(v)
    return f'{out} {unit}'


def fahrenheit_to_celsius(f: float) -> int:
    c = (f - 32) * 5 / 9
    # Oven temperatures are printed in steps of 5 in metric recipes;
    # keep internal/candy temperatures precise.
    return int(round(c / 5) * 5) if c >= 140 else int(round(c))


def _inches_to_metric(inches: float) -> Tuple[float, str]:
    cm = inches * 2.54
    if cm < 1:
        return max(1, round(cm * 10)), 'mm'
    if cm < 5:
        return round(cm, 1), 'cm'
    return round(cm), 'cm'


def _lookup_unit(unit_text: str) -> Optional[Tuple[str, float]]:
    unit_text = re.sub(r'\s+', ' ', unit_text.strip())
    for rx, base, factor in _UNIT_LOOKUP:
        if rx.match(unit_text):
            return base, factor
    return None


def _normalize_metric_unit(u: str) -> str:
    u = u.strip().lower()
    if u.startswith('mil'):
        return 'ml'
    if u.startswith('kilo') or u == 'kg':
        return 'kg'
    if u.startswith('lit') or u == 'l':
        return 'l'
    if u.startswith('centi') or u == 'cm':
        return 'cm'
    if u == 'mm':
        return 'mm'
    return 'g'


# ---------------------------------------------------------------------------
# regexes
# ---------------------------------------------------------------------------

_FLAGS = re.IGNORECASE

# "1 cup/240 milliliters", "4 ounces (115 grams)", "8 tablespoons/115 grams"
_DUAL_RE = re.compile(
    _NO_WORD_BEFORE + r'(?:' + QTY + r')[\s-]*(?:(?:' + DESCRIPTORS + r')\s+)?'
    r'(?:' + UNIT_ALT + r'|' + SPOON_ALT + r')' + _NO_LETTER_AFTER +
    r'\s*(?:/\s*(?P<a>' + QTY + r')\s*(?P<au>' + METRIC_ALT + r')' + _NO_LETTER_AFTER +
    r'|\(\s*(?:about\s+)?(?P<b>' + QTY + r')\s*(?P<bu>' + METRIC_ALT + r')\s*\))',
    _FLAGS,
)

# "½ cup (1 stick) butter" / "8 tablespoons (1 stick)"
_CUP_THEN_STICK_RE = re.compile(
    _NO_WORD_BEFORE + r'(?:' + QTY + r')\s*(?:' + UNIT_ALT + r'|tablespoons?|tbsps?\.?)'
    + _NO_LETTER_AFTER + r'\s*\(\s*(?P<n>' + QTY + r')\s*sticks?\s*\)',
    _FLAGS,
)
# "1 stick (½ cup) butter" / "2 sticks butter"
_STICK_RE = re.compile(
    _NO_WORD_BEFORE + r'(?P<n>' + QTY + r'|' + WORD_NUM + r')\s*sticks?' + _NO_LETTER_AFTER +
    r'(?:\s*\(\s*' + QTY + r'\s*(?:' + UNIT_ALT + r'|tablespoons?|tbsps?\.?)' + _NO_LETTER_AFTER +
    r'\s*\))?'
    r'(?=[^,;.]{0,40}?(?:butter|mantequilla|beurre|manteiga|margarin))',
    _FLAGS,
)

# "425 degrees", "350°F", "a 350-degree oven", "120 to 125 degrees F", "425 grados"
_TEMP_RE = re.compile(
    _NO_WORD_BEFORE + r'(?P<q>' + QTY + r')' + DEGREE_WORD +
    r'(?:\s*(?P<scale>F|Fahrenheit|C|Celsius|centigrade)' + _NO_LETTER_AFTER + r')?',
    _FLAGS,
)
_TEMP_F_ONLY_RE = re.compile(  # "425 F" without a degree sign
    _NO_WORD_BEFORE + r'(?P<q>' + QTY + r')\s*(?:F|Fahrenheit)\b(?!-)', 0,
)

# "9-by-13-inch", "9 x 13 inches", "8-by-8-by-2-inch"
_DIM_RE = re.compile(
    _NO_WORD_BEFORE + r'(?P<a>' + NUM + r')(?:-inch)?\s*(?:-?by-?|x|×)\s*(?P<b>' + NUM + r')'
    r'(?:(?:-inch)?\s*(?:-?by-?|x|×)\s*(?P<c>' + NUM + r'))?'
    r'[\s-]*(?:' + INCH_ALT + r')' + _NO_LETTER_AFTER + r'(?P<dash>-(?=[A-Za-z]))?',
    _FLAGS,
)
# "½-inch pieces", "2 to 3 inches", "1-inch-thick"
_INCH_RE = re.compile(
    _NO_WORD_BEFORE + r'(?P<q>' + QTY + r')[\s-]*(?:' + INCH_ALT + r')' + _NO_LETTER_AFTER +
    r'(?P<dash>-(?=[A-Za-z]))?',
    _FLAGS,
)

# Generic volume/weight: "2 cups", "1 to 1½ pounds", "6-ounce", "2 heaping cups", "a pound"
_UNIT_RE = re.compile(
    _NO_WORD_BEFORE + r'(?P<q>' + QTY + r'|\b' + WORD_NUM + r')[\s-]*'
    r'(?:(?P<desc>' + DESCRIPTORS + r')\s+)?'
    r'(?P<unit>' + UNIT_ALT + r')' + _NO_LETTER_AFTER,
    _FLAGS,
)

_CAPACITY_HINT = re.compile(r'^\)?\s*(?:ramekins?|glass(?:es)?|jars?|bottles?|mugs?|custard\s+cups?)', _FLAGS)
_MUFFIN_HINT = re.compile(r'^\s*(?:muffin|cupcake)', _FLAGS)


class UnitConverter:
    """Converts US/imperial cooking measurements to metric."""

    UNICODE_FRACTIONS = UNICODE_FRACTIONS

    def __init__(self, assume_fahrenheit: bool = True):
        """
        Args:
            assume_fahrenheit: treat bare temperatures ("Heat oven to 425 degrees",
                "350°") as Fahrenheit. True for US sources such as NYT Cooking.
                When False only explicit °F is converted (bare values >= 300 are
                still converted since no Celsius oven goes that high).
        """
        self.assume_fahrenheit = assume_fahrenheit

    # -- kept for backwards compatibility --------------------------------
    def convert_fraction_to_decimal(self, fraction_str: str) -> float:
        return parse_number(fraction_str)

    def fahrenheit_to_celsius(self, fahrenheit: float) -> int:
        return fahrenheit_to_celsius(fahrenheit)

    def convert_measurement(self, amount: float, unit: str) -> Tuple[float, str]:
        unit_lower = unit.lower().strip()
        if unit_lower in ('fahrenheit', '°f', 'f'):
            return fahrenheit_to_celsius(amount), '°C'
        found = _lookup_unit(unit_lower)
        if not found:
            return amount, unit
        values, metric_unit = _metric_values([amount], *found)
        return values[0], metric_unit

    # -- passes ----------------------------------------------------------
    @staticmethod
    def _dual(m: re.Match) -> str:
        qty = m.group('a') or m.group('b')
        unit = _normalize_metric_unit(m.group('au') or m.group('bu'))
        values, seps = _split_range(qty)
        return _join(values, seps, unit)

    @staticmethod
    def _sticks(m: re.Match) -> str:
        values, seps = _split_range(m.group('n'))
        grams, unit = _metric_values(values, 'g', STICK_GRAMS)
        return _join(grams, seps, unit)

    def _temperature(self, m: re.Match) -> str:
        scale = (m.group('scale') or '').lower()
        if scale.startswith('c'):
            return m.group(0)
        values, seps = _split_range(m.group('q'))
        explicit_f = scale.startswith('f')
        if not explicit_f:
            if not ((self.assume_fahrenheit and min(values) >= 100) or min(values) >= 300):
                return m.group(0)
        celsius = [fahrenheit_to_celsius(v) for v in values]
        return _join(celsius, seps, '°C')

    @staticmethod
    def _temp_f_only(m: re.Match) -> str:
        values, seps = _split_range(m.group('q'))
        return _join([fahrenheit_to_celsius(v) for v in values], seps, '°C')

    @staticmethod
    def _dims(m: re.Match) -> str:
        nums = [parse_number(m.group(k)) for k in ('a', 'b', 'c') if m.group(k)]
        cm = [_inches_to_metric(n) for n in nums]
        unit = 'mm' if all(u == 'mm' for _, u in cm) else 'cm'
        vals = [v if u == unit else (v / 10 if unit == 'cm' else v * 10) for v, u in cm]
        out = ' x '.join(fmt(v) for v in vals) + f' {unit}'
        return out + (' ' if m.group('dash') else '')

    @staticmethod
    def _inches(m: re.Match) -> str:
        values, seps = _split_range(m.group('q'))
        converted = [_inches_to_metric(v) for v in values]
        unit = converted[-1][1]
        vals = [v if u == unit else (v / 10 if unit == 'cm' else v * 10) for v, u in converted]
        return _join(vals, seps, unit) + (' ' if m.group('dash') else '')

    @staticmethod
    def _units(m: re.Match) -> str:
        unit_text = m.group('unit')
        found = _lookup_unit(unit_text)
        if not found:
            return m.group(0)
        base, factor = found
        tail = m.string[m.end():m.end() + 20]

        # "12-cup muffin tin" is a count of cups, not a volume.
        if base == 'ml' and factor == 240.0 and _MUFFIN_HINT.match(tail):
            return m.group(0)
        # "4 (6-ounce) ramekins" is a capacity -> ml, not g.
        if base == 'g' and factor == 28.35 and _CAPACITY_HINT.match(tail):
            base, factor = 'ml', 30.0

        values, seps = _split_range(m.group('q'))
        metric, unit = _metric_values(values, base, factor)
        out = _join(metric, seps, unit)
        if m.group('desc'):
            out = f"{out} ({m.group('desc')})"
        return out

    def convert_to_metric_only(self, text: str) -> str:
        """Convert every imperial measurement in ``text`` to metric (no originals kept)."""
        if not text or not isinstance(text, str):
            return text
        text = text.replace('⁄', '/')  # fraction slash: 1⁄2 -> 1/2
        text = _DUAL_RE.sub(self._dual, text)
        text = _CUP_THEN_STICK_RE.sub(self._sticks, text)
        text = _STICK_RE.sub(self._sticks, text)
        text = _TEMP_RE.sub(self._temperature, text)
        text = _TEMP_F_ONLY_RE.sub(self._temp_f_only, text)
        text = _DIM_RE.sub(self._dims, text)
        text = _INCH_RE.sub(self._inches, text)
        text = _UNIT_RE.sub(self._units, text)
        return re.sub(r'  +', ' ', text)

    def convert_text(self, text: str) -> str:
        """Convert a whole recipe text to metric. Kept for the CLI; metric only, so
        imperial units never leak into a translation through "(1 cup)" asides."""
        return self.convert_to_metric_only(text)


_converter_us = UnitConverter(assume_fahrenheit=True)
_converter_neutral = UnitConverter(assume_fahrenheit=False)

US_SOURCE_DOMAINS = ('nytimes.com', 'menshealth.com', 'seriouseats.com', 'bonappetit.com',
                     'epicurious.com', 'allrecipes.com', 'foodnetwork.com')


def is_us_source(source_url: Optional[str]) -> bool:
    return bool(source_url) and any(d in source_url.lower() for d in US_SOURCE_DOMAINS)


def convert_to_metric(text: str, assume_fahrenheit: bool = True) -> str:
    """Convert text to metric units (metric only, no originals in parentheses)."""
    conv = _converter_us if assume_fahrenheit else _converter_neutral
    return conv.convert_to_metric_only(text)


def convert_list_to_metric(items, assume_fahrenheit: bool = True) -> list:
    """Convert every string in a list; non-strings pass through untouched."""
    if not items:
        return items or []
    return [convert_to_metric(i, assume_fahrenheit) if isinstance(i, str) else i for i in items]
