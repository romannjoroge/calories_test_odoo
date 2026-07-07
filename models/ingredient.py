from odoo import models, fields

class Ingredient(models.Model):
    _inherit = 'product.template'

    calories = fields.Float(string='Calories (kcal)', digits='Product Unit of Measure', help='per 100g')
    protein = fields.Float(string='Protein (g)', digits='Product Unit of Measure', help='per 100g')
    fat = fields.Float(string='Fat (g)', digits='Product Unit of Measure', help='per 100g')
    carbs = fields.Float(string='Carbohydrates (g)', digits='Product Unit of Measure', help='per 100g')