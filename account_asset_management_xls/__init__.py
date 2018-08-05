# -*- coding: utf-8 -*-
try:
    from . import models
    from . import wizard
    from . import report
except ImportError:
    import logging
    logging.getLogger(__name__).warn(
        "report_xlsx_helpers not available in addons path")
