import logging
_logger = logging.getLogger(__name__)

def pre_init_hook(env):
    _logger.info(f"pre_init_hook(): Start")
    _logger.info(f"pre_init_hook(): End")

def post_init_hook(env):
    _logger.info(f"post_init_hook(): Start")
    _logger.info(f"post_init_hook(): End")

def uninstall_hook(env):
    _logger.info(f"uninstall_hook(): Start")
    _logger.info(f"uninstall_hook(): End")


def post_load(env):
    _logger.info(f"post_load(): Start")
    _logger.info(f"post_load(): End")