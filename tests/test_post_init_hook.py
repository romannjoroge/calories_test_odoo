from odoo.tests.common import TransactionCase
from ..hooks import _import_ingredients
import os
import tempfile

class TestPostInitHook(TransactionCase):
    # Constants that will be used in multiple tests
    
    def _write_csv(self, rows, fieldnames):
        """
        Helper function to create CSV file with data we can test for
        """
        import csv

        # Creates a temporary CSV file that we can use for testing
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.addCleanup(os.remove, path)
        return path
    
    def test_does_nothing_if_csv_not_found(self):
        # Setup
        non_exist_path = "/path/does/not/exist"

        # Call function with non existing path
        self.assertFalse(os.path.exists(non_exist_path))
        Product = self.env['product.template']
        count_before = Product.search_count([])
        _import_ingredients(self.env, non_exist_path)

        # No products should have been created
        count_after = Product.search_count([])
        self.assertEqual(count_after, count_before)

    def test_if_ingredients_created_successfully(self):
        test_code = "PRD-00001"
        test_product_name = "test"
        test_calories = 100
        test_proteins = 120
        test_fat = 80
        test_carbs = 75

        fieldNames = [
            'code',
            'product_name_en', 
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value',
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value',
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value',
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value',
        ]

        rows = [{
            'code': test_code,
            'product_name_en': test_product_name,
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value': str(test_calories),
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value': str(test_proteins),
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value': str(test_fat),
            'nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value': str(test_carbs)
        }]

        csv_path = self._write_csv(rows, fieldnames=fieldNames)

        Product = self.env['product.template']
        count_before = Product.search_count([])

        _import_ingredients(self.env, csv_path)

        # Asserting that item has been created
        count_after = Product.search_count([])
        self.assertEqual(count_after, count_before + 1)

        product = Product.search([('default_code', '=', test_code)], limit=1)
        self.assertTrue(product, "Product should have been created")
        self.assertEqual(product.name, test_product_name)
        self.assertEqual(product.calories, test_calories)
        self.assertEqual(product.protein, test_proteins)
        self.assertEqual(product.fat, test_fat)
        self.assertEqual(product.carbs, test_carbs)
        