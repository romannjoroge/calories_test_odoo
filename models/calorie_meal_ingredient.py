from odoo import fields, models


class CalorieMealIngredient(models.Model):
    _name = "calorie.meal.ingredient"
    _description = "Meal ingredient"

    meal_id = fields.Many2one(
        "calorie.meal.log",
        required=True,
        ondelete="cascade",
        string="Meal",
        index=True,
    )
    ingredient_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="restrict",
        string = "Ingredient",
    )
    quantity = fields.Float(required=True, default=1.0, string="Weight (g)")
