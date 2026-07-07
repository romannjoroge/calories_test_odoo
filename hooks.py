import logging
import os
import csv
_logger = logging.getLogger(__name__)

def _get_csv_path():
    """ 
    Function to return path of ingredients CSV
    """
    module_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_path, 'data', 'ingredients.csv')

def _read_csv_rows(csv_path):
    """Reads CSV rows, tolerating common Windows/Excel export encodings."""
    encodings_to_try = ('utf-8-sig', 'cp1252', 'latin-1')

    for encoding in encodings_to_try:
        try:
            with open(csv_path, encoding=encoding) as f:
                rows = list(csv.DictReader(f))
            return rows
        except UnicodeDecodeError:
            continue

    # If nothing worked, let it raise clearly rather than silently
    raise UnicodeDecodeError(
        'utf-8', b'', 0, 1, f"Could not decode {csv_path} with any of {encodings_to_try}"
    )

def _import_ingredients(env, path):
    """
    Function to import ingredients as products from the CSV file in the path
    """
    # Look for ingredients.csv file in data, if not found stop
    if not os.path.exists(path):
        _logger.info("Ingredients CSV file not found, skipping post init")
        return
    
    Product = env['product.template']
    created, skipped = 0, 0

    try:
        rows = _read_csv_rows(path)
    except UnicodeDecodeError:
        _logger.warning("Unable to import ingredients")
    else:
        for row in rows:
            sku = row.get('code', '').strip()
            if not sku:
                skipped += 1
                continue
            if Product.search([('default_code', '=', sku)], limit=1):
                skipped += 1
                continue

            # Get name
            if len(row.get('product_name_en', '').strip()) > 0:
                name = row.get('product_name_en', '').strip()
            elif len(row.get("product_name_fr", "").strip()) > 0:
                name = row.get("product_name_fr", "").strip()
            elif len(row.get("generic_name_en", "").strip()) > 0:
                name = row.get("generic_name_en", "").strip()
            elif len(row.get("generic_name_fr", "").strip()) > 0:
                name = row.get("generic_name_fr", "").strip()
            else:
                skipped += 1
                continue

            # Get Calories
            if len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value", "").strip()) > 0:
                calories = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value", "").strip())
            elif len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value_string", "").strip()) > 0:
                calories = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.energy-kcal.value_string", "").strip())
            else:
                calories = 0.0

            # Get protein
            if len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value", "").strip()) > 0:
                proteins = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value", "").strip())
            elif len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value_string", "").strip()) > 0:
                proteins = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.proteins.value_string", "").strip())
            else:
                proteins = 0

            # Get fats
            if len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value", "").strip()) > 0:
                fats = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value", "").strip())
            elif len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value_string", "").strip()) > 0:
                fats = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.fat.value_string", "").strip())
            else:
                fats = 0

            # Get carbs
            if len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value", "").strip()) > 0:
                carbs = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value", "").strip())
            elif len(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value_string", "").strip()) > 0:
                carbs = float(row.get("nutrition.input_sets.estimate.as_sold.100g.nutrients.carbohydrates.value_string", "").strip())
            else:
                carbs = 0

            Product.create({
                'name': name,
                'default_code': sku,
                'list_price': 0.0,
                'standard_price': 0.0,
                'type': 'consu',
                'calories': calories,
                'protein': proteins,
                'fat': fats,
                'carbs': carbs,
            })
            created += 1
        
        _logger.info("Product import: %s created, %s skipped", created, skipped)

def post_init_hook(env):
    """
    Function to take raw product data in CSV file in demo and create products
    for them after the module is installed
    """
    _logger.info("Starting to create products for ingredients")

    # Import data
    _import_ingredients(env, _get_csv_path())
    
