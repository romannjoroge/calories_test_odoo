from odoo import models, fields

class CalorieManagers(models.Model):
    """ 
    Model for managers of the calorie app
    """
    _name = "calories.managers"
    _description = "Managers of the calorie recommendation app"

    name = fields.Char(required=True, string="Full name")