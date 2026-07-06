{
    "name": "Calories Test Odoo",
    "summary": "Personal calorie budgeting, meal logging, and nutrition lookup",
    "version": "19.0.1.0.0",
    "author": "Roman Njoroge",
    "license": "OEEL-1",
    "depends": ["base", "product"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/calorie_profile_views.xml",
        "views/calorie_meal_log_views.xml",
        "views/calories_test_odoo_menus.xml",
    ],
    "demo": ["demo/data.xml"],
    "application": True,
    "category": "Tools",
    "post_init_hook": 'post_init_hook'
}