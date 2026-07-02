from odoo import models, fields

class UserData(models.Model):
    _name = "calories.users"
    _description = "Table to store the data entred by users"

    gender = fields.Selection(selection=[('M', "Male"), ('F', "Female")])
    age = fields.Integer()
    height = fields.Float(required=True)
    weight = fields.Float(required=True)
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
    calories = fields.Float(compute="_calculate_calories")

    def _calculate_calories(self):
        for rec in self:
            bmi = rec.weight / (rec.height * rec.height)

            if rec.physical_activity == "LIT":
                rec.calories = 1.2 * bmi
            elif rec.physical_activity == "LIG":
                rec.calories = 1.375 * bmi
            elif rec.physical_activity == "M":
                rec.calories = 1.55 * bmi
            elif rec.physical_activity == "V":
                rec.calories = 1.725 * bmi
            elif rec.physical_activity == "E":
                rec.calories = 1.9 * bmi
            else:
                rec.calories = 0
