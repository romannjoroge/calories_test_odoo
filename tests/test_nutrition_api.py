from unittest.mock import patch

import requests
from odoo.tests.common import TransactionCase


class TestNutritionApi(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.MealLog = self.env["calorie.meal.log"]
        self.Profile = self.env["calorie.profile"]

    def test_fetch_success(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })
        meal = self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "apple",
            "datetime_consumed": "2024-01-01 12:00:00",
        })
        fake_response = type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {"products": [{"nutriments": {"energy-kcal_100g": 52.0, "proteins_100g": 0.3, "carbohydrates_100g": 14.0, "fat_100g": 0.2}}]}})()
        with patch("odoo.addons.calories_test_odoo.controllers.nutrition_lookup.requests.get", return_value=fake_response) as mocked_get:
            meal.action_fetch_nutrition_data()
        self.assertEqual(meal.fetch_state, "fetched")
        self.assertEqual(meal.calories, 52.0)
        self.assertTrue(mocked_get.called)

    def test_fetch_not_found(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })
        meal = self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "unknown",
            "datetime_consumed": "2024-01-01 12:00:00",
        })
        fake_response = type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {"products": []}})()
        with patch("odoo.addons.calories_test_odoo.controllers.nutrition_lookup.requests.get", return_value=fake_response) as mocked_get:
            meal.action_fetch_nutrition_data()
        self.assertEqual(meal.fetch_state, "not_found")
        self.assertEqual(meal.error_message, "No nutrition information was found for this food.")
        self.assertTrue(mocked_get.called)

    def test_fetch_uses_supported_api_params(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })
        meal = self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "apple",
            "datetime_consumed": "2024-01-01 12:00:00",
        })
        fake_response = type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {"products": []}})()
        with patch("odoo.addons.calories_test_odoo.controllers.nutrition_lookup.requests.get", return_value=fake_response) as mocked_get:
            meal.action_fetch_nutrition_data()
        self.assertTrue(mocked_get.called)
        args, kwargs = mocked_get.call_args
        self.assertEqual(args[0], "https://world.openfoodfacts.org/api/v2/search")
        self.assertEqual(kwargs["params"]["search_terms"], "apple")
        self.assertEqual(kwargs["params"]["search_simple"], 1)
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertIn("calories_test_odoo", kwargs["headers"]["User-Agent"])

    def test_fetch_connection_error(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })
        meal = self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "apple",
            "datetime_consumed": "2024-01-01 12:00:00",
        })
        with patch("odoo.addons.calories_test_odoo.controllers.nutrition_lookup.requests.get", side_effect=requests.exceptions.Timeout("boom")) as mocked_get:
            meal.action_fetch_nutrition_data()
        self.assertEqual(meal.fetch_state, "error")
        self.assertIn("Unable to reach", meal.error_message)
        self.assertTrue(mocked_get.called)
