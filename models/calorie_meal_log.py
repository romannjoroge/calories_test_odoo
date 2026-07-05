import logging
import re

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CalorieMealLog(models.Model):
    _name = "calorie.meal.log"
    _description = "Meal log"

    profile_id = fields.Many2one(
        "calorie.profile",
        required=True,
        ondelete="cascade",
        string="Profile",
    )
    food_name = fields.Char(required=True, string="Food")
    ingredient_ids = fields.One2many(
        "calorie.meal.ingredient",
        "meal_id",
        string="Main ingredients",
    )
    datetime_consumed = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        string="Consumed at",
    )
    quantity = fields.Float(default=1.0, string="Quantity")
    calories = fields.Float(default=0.0, string="Calories")
    protein_g = fields.Float(default=0.0, string="Protein (g)")
    carbs_g = fields.Float(default=0.0, string="Carbs (g)")
    fat_g = fields.Float(default=0.0, string="Fat (g)")
    fetch_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("fetched", "Fetched"),
            ("not_found", "Not found"),
            ("error", "Error"),
        ],
        default="draft",
        string="Fetch state",
    )
    error_message = fields.Char(string="Message")

    @api.onchange("profile_id")
    def _onchange_profile_id(self):
        if self.profile_id:
            self.profile_id._compute_today_totals()

    def _parse_ingredient_names(self):
        ingredient_names = [ingredient.name.strip() for ingredient in self.ingredient_ids if ingredient.name and ingredient.name.strip()]
        if not ingredient_names:
            return [self.food_name] if self.food_name else []
        return ingredient_names

    def _fetch_nutrition_data(self, food_name):
        if not food_name:
            _logger.warning("Nutrition lookup skipped because no food name was provided.")
            return {
                "state": "error",
                "message": _("Please enter a food name to look up."),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        url = "https://world.openfoodfacts.org/api/v2/search"
        params = {
            "fields": "product_name,nutriments",
            "categories_tags_en": food_name,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("Nutrition lookup failed for %s: %s", food_name, exc)
            return {
                "state": "error",
                "message": _(
                    "Unable to reach the nutrition service right now. Please try again later."
                ),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        try:
            payload = response.json()
        except ValueError as exc:
            _logger.exception("Nutrition service returned invalid JSON for %s: %s", food_name, exc)
            return {
                "state": "error",
                "message": _("The nutrition service returned invalid data."),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        products = payload.get("products") or []
        if not products:
            _logger.info("Nutrition lookup returned no products for %s", food_name)
            return {
                "state": "not_found",
                "message": _("No nutrition information was found for this food."),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        product = products[0]
        nutriments = product.get("nutriments") or {}
        calories = (
            nutriments.get("energy-kcal_serving")
            or nutriments.get("energy-kcal_100g")
            or nutriments.get("energy-kcal")
            or 0.0
        )
        protein_g = (
            nutriments.get("proteins_serving")
            or nutriments.get("proteins_100g")
            or 0.0
        )
        carbs_g = (
            nutriments.get("carbohydrates_serving")
            or nutriments.get("carbohydrates_100g")
            or 0.0
        )
        fat_g = nutriments.get("fat_serving") or nutriments.get("fat_100g") or 0.0

        return {
            "state": "fetched",
            "message": False,
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
        }

    def action_fetch_nutrition_data(self):
        for record in self:
            ingredient_names = record._parse_ingredient_names()
            _logger.info("Fetching nutrition data for meal %s with ingredients %s", record.id, ingredient_names)
            if not ingredient_names:
                ingredient_names = [record.food_name]

            aggregated = {
                "state": "fetched",
                "message": False,
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }
            last_message = False
            fetched_any = False
            for ingredient_name in ingredient_names:
                result = record._fetch_nutrition_data(ingredient_name)
                aggregated["calories"] += result["calories"]
                aggregated["protein_g"] += result["protein_g"]
                aggregated["carbs_g"] += result["carbs_g"]
                aggregated["fat_g"] += result["fat_g"]
                if result["state"] == "fetched":
                    fetched_any = True
                elif not last_message and result["message"]:
                    last_message = result["message"]

            if not fetched_any:
                aggregated["state"] = "error" if last_message else "not_found"
                aggregated["message"] = last_message or _("No nutrition information was found for the provided ingredients.")
                _logger.warning("Nutrition aggregation failed for meal %s: %s", record.id, aggregated["message"])
            else:
                aggregated["message"] = False
                _logger.info("Nutrition aggregation completed for meal %s", record.id)

            record.write(
                {
                    "fetch_state": aggregated["state"],
                    "error_message": aggregated["message"],
                    "calories": aggregated["calories"],
                    "protein_g": aggregated["protein_g"],
                    "carbs_g": aggregated["carbs_g"],
                    "fat_g": aggregated["fat_g"],
                }
            )
            if record.profile_id:
                record.profile_id._compute_today_totals()
