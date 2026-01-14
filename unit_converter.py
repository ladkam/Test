"""
Unit conversion module for converting imperial measurements to metric.
"""
import re
from typing import Tuple, Optional


class UnitConverter:
    """Converts imperial cooking measurements to metric."""

    # Conversion factors
    CONVERSIONS = {
        # Volume
        'cup': ('ml', 236.588),
        'cups': ('ml', 236.588),
        'tablespoon': ('ml', 14.787),
        'tablespoons': ('ml', 14.787),
        'tbsp': ('ml', 14.787),
        'teaspoon': ('ml', 4.929),
        'teaspoons': ('ml', 4.929),
        'tsp': ('ml', 4.929),
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
        'fahrenheit': ('celsius', None),
        'f': ('celsius', None),
        '°f': ('celsius', None),
    }

    def __init__(self):
        # Pattern to match measurements like "2 cups", "1/2 teaspoon", "350°F"
        self.measurement_pattern = re.compile(
            r'(\d+(?:/\d+)?(?:\.\d+)?)\s*(?:to\s+\d+(?:/\d+)?(?:\.\d+)?\s*)?'
            r'(cup|cups|tablespoon|tablespoons|tbsp|teaspoon|teaspoons|tsp|'
            r'fluid ounce|fluid ounces|fl oz|pint|pints|quart|quarts|gallon|gallons|'
            r'ounce|ounces|oz|pound|pounds|lb|lbs|°f|fahrenheit|f)\b',
            re.IGNORECASE
        )

    def convert_fraction_to_decimal(self, fraction_str: str) -> float:
        """Convert a fraction string like '1/2' or '2.5' to decimal."""
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

        # Handle temperature separately
        if unit_lower in ['fahrenheit', 'f', '°f']:
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
