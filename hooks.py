import logging
_logger = logging.getLogger(__name__)

def post_init_hook(env):
    """
    Function to take raw product data in CSV file in demo and create products
    for them after the module is installed
    """
    _logger.info("Starting to create products for ingredients")
