"""
Unit conversion module for converting imperial measurements to metric.
"""
import re
from typing import Tuple, Optional


class UnitConverter:
    """Converts imperial cooking measurements to metric."""

    # Unicode fraction mappings
    UNICODE_FRACTIONS = {
        '½': 0.5,
        '¼': 0.25,
        '¾': 0.75,
        '⅓': 1/3,
        '⅔': 2/3,
        '⅛': 0.125,
        '⅜': 0.375,
        '⅝': 0.625,
        '⅞': 0.875,
        '⅕': 0.2,
        '⅖': 0.4,
        '⅗': 0.6,
        '⅘': 0.8,
        '⅙': 1/6,
        '⅚': 5/6,
    }

    # Conversion factors
    # Note: teaspoon/tablespoon are universal and not converted
    CONVERSIONS = {
        # Volume
        'cup': ('ml', 236.588),
        'cups': ('ml', 236.588),
        'fluid ounce': ('ml', 29.574),
        'fluid ounces': ('ml', 29.574),
        'fl oz': ('ml', 29.574),
        'pint': ('ml', 473.176),
        'pints': ('ml', 473.176),
        'quart': ('l', 0.946),
        'quarts': ('l', 0.946),
        'gallon': ('l', 3.785),
        'gallons': ('l', 3.785),

        # Weight
        'ounce': ('g', 28.350),
        'ounces': ('g', 28.350),
        'oz': ('g', 28.350),
        'pound': ('g', 453.592),
        'pounds': ('g', 453.592),
        'lb': ('g', 453.592),
        'lbs': ('g', 453.592),

        # Temperature (special case, handled separately)
        # Only convert explicitly marked Fahrenheit to avoid misconverting Celsius
        'fahrenheit': ('celsius', None),
        '°f': ('celsius', None),
    }

    def __init__(self):
        # Unicode fraction characters for pattern matching
        unicode_fracs = ''.join(self.UNICODE_FRACTIONS.keys())

        # Pattern to match measurements like "2 cups", "2¼ cups", "350°F", "6-ounce"
        # Supports: integers, decimals, fractions (1/2), unicode fractions (½),
        # and mixed numbers (2¼, 2 1/2). Allows hyphen or space between number and unit.
        # Note: teaspoon/tablespoon are universal and not matched for conversion
        self.measurement_pattern = re.compile(
            r'(\d+[' + unicode_fracs + r']|\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?[' + unicode_fracs + r']?)[\s-]*'
            r'(cup|cups|fluid ounce|fluid ounces|fl oz|pint|pints|quart|quarts|gallon|gallons|'
            r'ounce|ounces|oz|pound|pounds|lb|lbs|°f|fahrenheit)\b',
            re.IGNORECASE
        )

    def convert_fraction_to_decimal(self, fraction_str: str) -> float:
        """Convert a fraction string like '1/2', '2.5', '2¼', or '2 1/2' to decimal."""
        fraction_str = fraction_str.strip()

        # Check for Unicode fractions in the string
        for unicode_frac, value in self.UNICODE_FRACTIONS.items():
            if unicode_frac in fraction_str:
                # Handle mixed numbers like "2¼"
                whole_part = fraction_str.replace(unicode_frac, '').strip()
                if whole_part:
                    return float(whole_part) + value
                return value

        # Handle mixed numbers like "2 1/2"
        if ' ' in fraction_str and '/' in fraction_str:
            parts = fraction_str.split()
            whole = float(parts[0])
            frac_parts = parts[1].split('/')
            return whole + float(frac_parts[0]) / float(frac_parts[1])

        # Handle simple fractions like "1/2"
        if '/' in fraction_str:
            parts = fraction_str.split('/')
            return float(parts[0]) / float(parts[1])

        return float(fraction_str)

    def fahrenheit_to_celsius(self, fahrenheit: float) -> int:
        """Convert Fahrenheit to Celsius."""
        return round((fahrenheit - 32) * 5/9)

    def convert_measurement(self, amount: float, unit: str) -> Tuple[float, str]:
        """
        Convert a measurement to metric.

        Args:
            amount: The quantity
            unit: The unit to convert from

        Returns:
            Tuple of (converted_amount, metric_unit)
        """
        unit_lower = unit.lower().strip()

        # Handle temperature separately (only explicit Fahrenheit)
        if unit_lower in ['fahrenheit', '°f']:
            celsius = self.fahrenheit_to_celsius(amount)
            return celsius, '°C'

        # Handle other conversions
        if unit_lower in self.CONVERSIONS:
            metric_unit, factor = self.CONVERSIONS[unit_lower]
            converted = amount * factor

            # Convert large ml to liters
            if metric_unit == 'ml' and converted >= 1000:
                return round(converted / 1000, 2), 'l'

            # Convert large grams to kg
            if metric_unit == 'g' and converted >= 1000:
                return round(converted / 1000, 2), 'kg'

            # Round appropriately
            if converted < 10:
                return round(converted, 1), metric_unit
            else:
                return round(converted), metric_unit

        return amount, unit

    def convert_text(self, text: str) -> str:
        """
        Convert all imperial measurements in text to metric.

        Args:
            text: Text containing measurements

        Returns:
            Text with imperial measurements converted to metric
        """
        def replace_measurement(match):
            amount_str = match.group(1)
            unit = match.group(2)

            try:
                amount = self.convert_fraction_to_decimal(amount_str)
                converted_amount, metric_unit = self.convert_measurement(amount, unit)

                # Format the output
                if isinstance(converted_amount, int):
                    return f"{converted_amount} {metric_unit} ({amount_str} {unit})"
                else:
                    return f"{converted_amount} {metric_unit} ({amount_str} {unit})"
            except (ValueError, ZeroDivisionError):
                return match.group(0)  # Return original if conversion fails

        return self.measurement_pattern.sub(replace_measurement, text)

    def convert_to_metric_only(self, text: str) -> str:
        """
        Convert all imperial measurements in text to metric (without showing original).

        Args:
            text: Text containing measurements

        Returns:
            Text with imperial measurements converted to metric only
        """
        if not text:
            return text

        def replace_measurement(match):
            amount_str = match.group(1)
            unit = match.group(2)

            try:
                amount = self.convert_fraction_to_decimal(amount_str)
                converted_amount, metric_unit = self.convert_measurement(amount, unit)

                # Format the output (metric only, no original)
                if isinstance(converted_amount, float) and converted_amount == int(converted_amount):
                    converted_amount = int(converted_amount)
                return f"{converted_amount} {metric_unit}"
            except (ValueError, ZeroDivisionError):
                return match.group(0)  # Return original if conversion fails

        return self.measurement_pattern.sub(replace_measurement, text)


# Global converter instance
_converter = UnitConverter()


def convert_to_metric(text: str) -> str:
    """
    Convenience function to convert text to metric units.

    Args:
        text: Text containing measurements

    Returns:
        Text with all imperial measurements converted to metric
    """
    return _converter.convert_to_metric_only(text)
