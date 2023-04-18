# simple tests

from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """Test calc functions"""

    def test_add_numbers(self):
        res = calc.add(5, 6)
        self.assertEqual(res, 11)

    def test_subtract_numbers(self):
        res = calc.subtract(2, 1)
        self.assertEqual(res, 1)
