import logging

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
        translate = self.env._ if self.env else _

        if not food_name:
            if _logger.isEnabledFor(logging.WARNING):
                _logger.warning("Nutrition lookup skipped because no food name was provided.")
            return {
                "state": "error",
                "message": translate("Please enter a food name to look up."),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        request_headers = {
            "User-Agent": "calories_test_odoo/1.0 (+https://example.com)",
            "Accept": "application/json",
        }
        request_params = {
            "search_terms": food_name,
            "search_simple": 1,
            "fields": "product_name,nutriments",
            "page_size": 1,
        }

        try:
            response = requests.get(
                "https://world.openfoodfacts.org/api/v2/search",
                params=request_params,
                headers=request_headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            if _logger.isEnabledFor(logging.WARNING):
                _logger.warning("Nutrition lookup failed for %s using v2 search: %s", food_name, exc)
            try:
                response = requests.get(
                    "https://world.openfoodfacts.org/cgi/search.pl",
                    params={
                        **request_params,
                        "json": 1,
                    },
                    headers=request_headers,
                    timeout=10,
                )
                response.raise_for_status()
            except requests.RequestException as fallback_exc:
                if _logger.isEnabledFor(logging.ERROR):
                    _logger.exception(
                        "Nutrition lookup failed for %s using fallback endpoint: %s",
                        food_name,
                        fallback_exc,
                    )
                return {
                    "state": "error",
                    "message": translate(
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
            if _logger.isEnabledFor(logging.ERROR):
                _logger.exception("Nutrition service returned invalid JSON for %s: %s", food_name, exc)
            return {
                "state": "error",
                "message": translate("The nutrition service returned invalid data."),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

        products = payload.get("products") or []
        if not products:
            if _logger.isEnabledFor(logging.INFO):
                _logger.info("Nutrition lookup returned no products for %s", food_name)
            return {
                "state": "not_found",
                "message": translate("No nutrition information was found for this food."),
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
            if _logger.isEnabledFor(logging.INFO):
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
                aggregated["calories"] += result.get("calories", 0.0)
                aggregated["protein_g"] += result.get("protein_g", 0.0)
                aggregated["carbs_g"] += result.get("carbs_g", 0.0)
                aggregated["fat_g"] += result.get("fat_g", 0.0)

                result_state = result.get("state", "error")
                if result_state == "fetched":
                    fetched_any = True
                elif result_state == "error":
                    aggregated["state"] = "error"
                    aggregated["message"] = result.get("message") or aggregated["message"]
                elif result_state == "not_found" and aggregated["state"] != "error":
                    aggregated["state"] = "not_found"
                    aggregated["message"] = result.get("message") or aggregated["message"]

                if not last_message and result.get("message"):
                    last_message = result["message"]

            # Multiply aggregated calories, protein etc by quantity 
            aggregated["calories"] *= record.quantity
            aggregated["protein_g"] *= record.quantity
            aggregated["carbs_g"] *= record.quantity
            aggregated["fat_g"] *= record.quantity

            if not fetched_any:
                if aggregated["state"] == "fetched":
                    aggregated["state"] = "not_found"
                if not aggregated["message"]:
                    aggregated["message"] = last_message or _("No nutrition information was found for the provided ingredients.")
                if _logger.isEnabledFor(logging.WARNING):
                    _logger.warning("Nutrition aggregation failed for meal %s: %s", record.id, aggregated["message"])
            else:
                aggregated["message"] = False
                if _logger.isEnabledFor(logging.INFO):
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
