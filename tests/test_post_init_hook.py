from odoo.tests.common import TransactionCase
from ..hooks import _import_ingredients
import os

class TestPostInitHook(TransactionCase):
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
        