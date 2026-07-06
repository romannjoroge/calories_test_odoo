import logging
import os
_logger = logging.getLogger(__name__)

def _get_csv_path():
    """ 
    Function to return path of ingredients CSV
    """
    module_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_path, 'data', 'ingredients.csv')

def _import_ingredients(env, path):
    """
    Function to import ingredients as products from the CSV file in the path
    """
    # Look for ingredients.csv file in data, if not found stop
    if not os.path.exists(path):
        _logger.info("Ingredients CSV file not found, skipping post init")
        return

def post_init_hook(env):
    """
    Function to take raw product data in CSV file in demo and create products
    for them after the module is installed
    """
    _logger.info("Starting to create products for ingredients")

    # Import data
    _import_ingredients(env, _get_csv_path())
    
