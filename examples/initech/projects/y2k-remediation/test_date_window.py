import unittest

from date_window import WindowError, days_between, expand_year, parse_yymmdd


class ExpandYearTest(unittest.TestCase):
    def test_below_pivot_is_2000s(self):
        self.assertEqual(expand_year(0), 2000)
        self.assertEqual(expand_year(49), 2049)

    def test_at_or_above_pivot_is_1900s(self):
        self.assertEqual(expand_year(50), 1950)
        self.assertEqual(expand_year(99), 1999)

    def test_rejects_three_digits(self):
        with self.assertRaises(WindowError):
            expand_year(100)


class ParseTest(unittest.TestCase):
    def test_new_years_eve_to_new_years_day(self):
        self.assertEqual(days_between("991231", "000101"), 1)

    def test_bad_input(self):
        with self.assertRaises(WindowError):
            parse_yymmdd("1999-12-31")


if __name__ == "__main__":
    unittest.main()
