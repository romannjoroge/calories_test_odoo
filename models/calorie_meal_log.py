import logging

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CalorieMealLog(models.Model):
    _name = "calorie.meal.log"
    _description = "Meal log"
    _order = "datetime_consumed desc"

    profile_id = fields.Many2one(
        "calorie.profile",
        required=True,
        ondelete="cascade",
        string="Profile",
        default= lambda self: self.env["calorie.profile"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
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

    @api.onchange("ingredient_ids", "ingredient_ids.ingredient_id", "ingredient_ids.quantity")
    def _onchange_ingredients(self):
        """
        Function to get new nutrition data of meal as ingredients change
        """
        for meal in self:
            # Reset nutrition details to zero
            meal.calories = 0
            meal.protein_g = 0
            meal.carbs_g = 0
            meal.fat_g = 0

            error_fetching_encountered = False

            # For each ingredient
            for ingredient in meal.ingredient_ids:
                ingredient_quantity_multiplier = ingredient.quantity / 100 # since nutrition values are per 100g

                # If ingredient has no stored nutritional details
                if (ingredient.ingredient_id.calories == 0 and ingredient.ingredient_id.protein == 0 and ingredient.ingredient_id.carbs == 0 and ingredient.ingredient_id.fat == 0):
                    # Get ingredients from internet
                    try:
                        details = meal._fetch_nutrition_data(ingredient.ingredient_id.name)    
                    except Exception:
                        # Notify user that nutrition details couldn't be found
                        meal._notify_fetch_result(_("Could not get nutrition details for the ingredient %s", ingredient.ingredient_id.name))
                        error_fetching_encountered = True
                    else:
                        # If details couldn't be gotten go with defaults
                        if details["state"] != "fetched":
                            error_fetching_encountered = True
                            meal._notify_fetch_result(
                                details["message"] if details["message"] else _("Could not get nutrition details"),
                                title=_("Nutrition fetch") if details["state"] == "error" else _("Nutrition data not found"),
                            )
                            meal.fetch_state = details["state"]
                            meal.error_message = details["message"] if details["message"] else _("Could not get meal details")
                        else:
                            meal.fetch_state = details["state"]
                            meal.error_message = details["message"]
                            meal.calories += details["calories"] * ingredient_quantity_multiplier
                            meal.protein_g += details["protein_g"] * ingredient_quantity_multiplier
                            meal.carbs_g += details["carbs_g"] * ingredient_quantity_multiplier
                            meal.fat_g += details["fat_g"] * ingredient_quantity_multiplier
                else:
                    meal.calories += ingredient.ingredient_id.calories * ingredient_quantity_multiplier
                    meal.protein_g += ingredient.ingredient_id.protein * ingredient_quantity_multiplier
                    meal.carbs_g += ingredient.ingredient_id.carbs * ingredient_quantity_multiplier
                    meal.fat_g += ingredient.ingredient_id.fat * ingredient_quantity_multiplier

            if not error_fetching_encountered:
                meal.fetch_state = "fetched"

    @api.onchange("profile_id")
    def _onchange_profile_id(self):
        if self.profile_id:
            self.profile_id._compute_today_totals()

    def _parse_ingredient_names(self):
        ingredient_names = [ingredient.ingredient_id.name.strip() for ingredient in self.ingredient_ids if ingredient.ingredient_id.name and ingredient.ingredient_id.name.strip()]
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
                "message": translate("Please choose an ingredient to look up."),
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
            "categories_tags_en": food_name,
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
        except requests.HTTPError as exc:
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
        except requests.RequestException as exc:
            if _logger.isEnabledFor(logging.ERROR):
                _logger.exception(
                    "Nutrition lookup failed for %s using fallback endpoint: %s",
                    food_name,
                    exc,
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

    def _notify_fetch_result(self, message, title=None):
        if not message:
            return
        try:
            # Prefer the bus notification if available (real-time popup)
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': title or _('Nutrition fetch notice'),
                'message': message,
                'type': 'warning',
            })
        except Exception:
            # Fallback: post a partner message so the information is visible
            try:
                partner = self.env.user.partner_id
                partner.message_post(body=message, subject=title or _('Nutrition fetch notice'))
            except Exception:
                # As a last resort, log the message (silent in normal tests)
                if _logger.isEnabledFor(logging.INFO):
                    _logger.info("Notification fallback: %s", message)