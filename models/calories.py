from odoo import models, fields, api

class UserData(models.Model):
    _name = "calories.users"
    _description = "Table to store the data entred by users"

    gender = fields.Selection(selection=[('M', "Male"), ('F', "Female")])
    age = fields.Integer()
    height = fields.Float(required=True, string="Height (m)")
    weight = fields.Float(required=True, string="Weight (kg)")
    physical_activty = fields.Selection(selection=[
        ("LIT", "Little exercise"),
        ("LIG", "Light exercise"),
        ("M", "Moderate exercise (3-5 days/wk)"),
        ("V", "Very active"),
        ("E", "Extra active")
    ], required=True, string="Physical Activity", default="LIT")
    goal = fields.Selection(selection=[
        ("LOSS", "Weight Loss")
    ], default="LOSS")
    calories = fields.Float(compute="_calculate_calories", string="Recommended Calories", store=True)

    @api.depends('weight', 'height', 'physical_activty')
    def _calculate_calories(self):
        for rec in self:
            if not rec.height or not rec.weight:
                rec.calories = 0
                continue
            try:
                bmi = rec.weight / (rec.height * rec.height)
            except ZeroDivisionError:
                rec.calories = 0
                continue
            if rec.physical_activty == "LIT":
                rec.calories = 1.2 * bmi
            elif rec.physical_activty == "LIG":
                rec.calories = 1.375 * bmi
            elif rec.physical_activty == "M":
                rec.calories = 1.55 * bmi
            elif rec.physical_activty == "V":
                rec.calories = 1.725 * bmi
            elif rec.physical_activty == "E":
                rec.calories = 1.9 * bmi
            else:
                rec.calories = 0
