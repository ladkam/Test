"""Tests for the imperial -> metric converter, using real NYT Cooking phrasing."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unit_converter import convert_to_metric  # noqa: E402

CASES = [
    # plain volumes / weights
    ('2 cups all-purpose flour', '480 ml all-purpose flour'),
    ('¼ cup olive oil', '60 ml olive oil'),
    ('1 1/2 cups milk', '360 ml milk'),
    ('1⁄2 cup sugar', '120 ml sugar'),
    ('1½ pounds shrimp', '680 g shrimp'),
    ('1 lb. ground beef', '450 g ground beef'),
    ('8 oz. mushrooms', '225 g mushrooms'),
    ('2 1/2 pounds beef chuck', '1.1 kg beef chuck'),
    ('1 quart water', '950 ml water'),
    # ranges convert both ends
    ('1 to 1½ pounds boneless chicken thighs', '450 to 680 g boneless chicken thighs'),
    # NYT dual units: keep NYT's own metric figure
    ('1 cup/240 milliliters heavy cream', '240 ml heavy cream'),
    ('1 cup/130 grams all-purpose flour', '130 g all-purpose flour'),
    ('4 ounces (115 grams) cream cheese', '115 g cream cheese'),
    # butter sticks
    ('1 stick (½ cup) unsalted butter, softened', '115 g unsalted butter, softened'),
    ('½ cup (1 stick) unsalted butter', '115 g unsalted butter'),
    ('1 cinnamon stick', '1 cinnamon stick'),
    # package sizes
    ('1 (14-ounce) can coconut milk', '1 (400 g) can coconut milk'),
    ('Divide among 4 (6-ounce) ramekins.', 'Divide among 4 (180 ml) ramekins.'),
    # NYT's bracketed weights beat converted volumes (real NYT lines)
    ('2 cups minus 2 tablespoons cake flour (8 ½ ounces)', '240 g cake flour'),
    ('1 ¼ cups light brown sugar (10 ounces)', '280 g light brown sugar'),
    ('1 ¼ cups unsalted butter (2 ½ sticks)', '280 g unsalted butter'),
    ('1 to 2 cups (4 to 8 ounces) grated cheese', '115 to 225 g grated cheese'),
    ('1 cup plus 2 tablespoons sugar', '270 ml sugar'),
    ('Scoop 6 3 ½-ounce mounds of dough', 'Scoop 6 (100 g) mounds of dough'),
    # spoons stay spoons
    ('3 tablespoons olive oil', '3 tablespoons olive oil'),
    ('1 teaspoon kosher salt', '1 teaspoon kosher salt'),
    # temperatures (NYT omits the F)
    ('Heat oven to 425 degrees.', 'Heat oven to 220 °C.'),
    ('Preheat the oven to 350°F.', 'Preheat the oven to 175 °C.'),
    ('Bake in a 350-degree oven.', 'Bake in a 175 °C oven.'),
    ('Roast until 120 to 125 degrees.', 'Roast until 49 to 52 °C.'),
    ('Rotate the pan 90 degrees.', 'Rotate the pan 90 degrees.'),
    ('Heat to 200°C.', 'Heat to 200°C.'),
    # sizes
    ('Line a 9-by-13-inch baking dish.', 'Line a 23 x 33 cm baking dish.'),
    ('Cut into 1- to 2-inch pieces.', 'Cut into 2.5 to 5 cm pieces.'),
    ('Pound to ¼-inch-thick cutlets.', 'Pound to 6 mm thick cutlets.'),
    ('Heat a 12-inch skillet.', 'Heat a 30 cm skillet.'),
    ('Line a 12-cup muffin tin.', 'Line a 12-cup muffin tin.'),
    # words as numbers
    ('Add about a pound of shrimp.', 'Add about 450 g of shrimp.'),
    ('Stir in half a cup of broth.', 'Stir in 120 ml of broth.'),
    ('Serve at once.', 'Serve at once.'),
    # safety net on AI output
    ('2 tazas de harina', '480 ml de harina'),
    ('media taza de azúcar', '120 ml de azúcar'),
    ('1 a 1½ libras de pollo', '450 a 680 g de pollo'),
    ('Precalentar el horno a 425 grados.', 'Precalentar el horno a 220 °C.'),
    ('une tasse de lait', '240 ml de lait'),
    ('Corta en trozos de 1 pulgada.', 'Corta en trozos de 2.5 cm.'),
]


@pytest.mark.parametrize('source,expected', CASES)
def test_converts_to_metric(source, expected):
    assert convert_to_metric(source) == expected


@pytest.mark.parametrize('source,_', CASES)
def test_idempotent(source, _):
    once = convert_to_metric(source)
    assert convert_to_metric(once) == once


def test_bare_degrees_not_assumed_fahrenheit_for_non_us_sources():
    assert convert_to_metric('Heat oven to 200 degrees.', assume_fahrenheit=False) == 'Heat oven to 200 degrees.'
    # nothing Celsius gets that hot, so this is unambiguous
    assert convert_to_metric('Heat oven to 450 degrees.', assume_fahrenheit=False) == 'Heat oven to 230 °C.'


def test_repair_old_half_converted_ranges():
    from metric_backfill import repair_ranges
    assert repair_ranges('1 a 680 g de pollo', '450 to 680 g chicken') == '450 a 680 g de pollo'
    assert repair_ranges('450 a 680 g de pollo', '450 to 680 g chicken') == '450 a 680 g de pollo'
    assert repair_ranges('Asar hasta 120 a 52 °C', 'Roast until 49 to 52 °C') == 'Asar hasta 49 a 52 °C'
