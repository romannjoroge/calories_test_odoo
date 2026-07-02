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


    
