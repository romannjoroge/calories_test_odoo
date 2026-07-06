import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CalorieProfile(models.Model):
    _name = "calorie.profile"
    _description = "Calorie profile"
    _rec_name = "user_id"

    user_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="cascade",
        default=lambda self: self.env.user,
        string="User",
    )

    _unique_profile_user_id = models.Constraint("UNIQUE(user_id)", "A calorie profile already exists for this user")

    sex = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        required=True,
        default="male",
        string="Sex",
    )
    age = fields.Integer(required=True, default=30, string="Age")
    height_cm = fields.Float(required=True, default=175.0, string="Height (cm)")
    weight_kg = fields.Float(required=True, default=70.0, string="Weight (kg)")
    activity_level = fields.Selection(
        [
            ("sedentary", "Sedentary"),
            ("light", "Light"),
            ("moderate", "Moderate"),
            ("active", "Active"),
            ("very_active", "Very active"),
        ],
        required=True,
        default="sedentary",
        string="Activity level",
    )
    goal = fields.Selection(
        [
            ("maintain", "Maintain"),
            ("lose", "Lose weight"),
            ("gain", "Gain weight"),
        ],
        required=True,
        default="maintain",
        string="Goal",
    )
    daily_calorie_budget = fields.Float(
        string="Daily calorie budget",
        compute="_compute_budget",
        readonly=True,
        store=False,
    )
    calories_consumed_today = fields.Float(
        string="Calories consumed today",
        compute="_compute_today_totals",
        readonly=True,
        store=False,
    )
    calories_remaining_today = fields.Float(
        string="Calories remaining today",
        compute="_compute_today_totals",
        readonly=True,
        store=False,
    )
    calories_consumed_progress = fields.Float(
        string="Calories consumed progress",
        compute="_compute_today_totals",
        readonly=True,
        store=False,
    )
    meal_ids = fields.One2many(
        "calorie.meal.log",
        "profile_id",
        string="Meals",
    )
    active = fields.Boolean(default=True)


    @api.depends("age", "sex", "height_cm", "weight_kg", "activity_level", "goal")
    def _compute_budget(self):
        for record in self:
            record.daily_calorie_budget = record._compute_calorie_budget(
                record.sex,
                record.age,
                record.height_cm,
                record.weight_kg,
                record.activity_level,
                record.goal,
            )

    @api.depends("meal_ids", "meal_ids.datetime_consumed", "meal_ids.calories")
    def _compute_today_totals(self):
        for record in self:
            today = fields.Date.context_today(record)
            start_dt = fields.Datetime.to_datetime(f"{today} 00:00:00")
            end_dt = start_dt + timedelta(days=1)
            profile_id = record.id if isinstance(record.id, int) else record.id
            meal_logs = self.env["calorie.meal.log"].search(
                [
                    ("profile_id", "=", profile_id),
                    ("datetime_consumed", ">=", start_dt),
                    ("datetime_consumed", "<", end_dt),
                ]
            )
            consumed = sum(log.calories or 0.0 for log in meal_logs)
            record.calories_consumed_today = consumed
            record.calories_remaining_today = record.daily_calorie_budget - consumed
            record.calories_consumed_progress = (
                0.0 if record.daily_calorie_budget <= 0 else min(100.0, (consumed / record.daily_calorie_budget) * 100.0)
            )

    @api.onchange("age", "sex", "height_cm", "weight_kg", "activity_level", "goal")
    def _onchange_profile_data(self):
        self._compute_budget()
        self._compute_today_totals()

    def _compute_calorie_budget(self, sex, age, height_cm, weight_kg, activity_level, goal):
        if not sex or age is None or height_cm is None or weight_kg is None:
            return 0.0

        age = max(int(age), 0)
        height_cm = max(float(height_cm), 0.0)
        weight_kg = max(float(weight_kg), 0.0)

        if age <= 0 or height_cm <= 0.0 or weight_kg <= 0.0:
            return 0.0

        if sex == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 161

        multiplier = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }.get(activity_level, 1.2)

        tdee = bmr * multiplier
        if goal == "lose":
            return max(tdee - 500, 1200.0)
        if goal == "gain":
            return max(tdee + 500, 0.0)
        return max(tdee, 0.0)
