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
    name = fields.Char(required=True, string="Ingredient", index=True)
