{
    "name": "calories_test_odoo",
    "summary": "Test application for recommending number of calories someone should take",
    "version": "19.0.0.0.0",
    "author": "Roman Njoroge",
    "license": "OEEL-1",
    "depends": ["base"],
    "data": [
        # Security
        "security/res_groups.xml",
        "security/ir.model.access.csv",

        # Views
        "views/calories_users_view.xml",

        # Menus
        "views/calories_menus.xml"
    ],
    "demo": ["demo/data.xml"]
}