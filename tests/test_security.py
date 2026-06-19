import unittest

from schedule import safe_cell_value, safe_excel_value


class SecurityTests(unittest.TestCase):
    def test_safe_cell_value_escapes_formula_prefixes(self):
        self.assertEqual(safe_cell_value('=SUM(A1:A2)'), "'=SUM(A1:A2)")
        self.assertEqual(safe_cell_value('+1+1'), "'+1+1")
        self.assertEqual(safe_cell_value('-1+1'), "'-1+1")
        self.assertEqual(safe_cell_value('@HYPERLINK("x")'), '\'@HYPERLINK("x")')

    def test_safe_excel_value_preserves_numbers_and_escapes_strings(self):
        self.assertEqual(safe_excel_value(42), 42)
        self.assertEqual(safe_excel_value(3.14), 3.14)
        self.assertEqual(safe_excel_value('=1+1'), "'=1+1")
        self.assertEqual(safe_excel_value(None), '')


if __name__ == '__main__':
    unittest.main()
