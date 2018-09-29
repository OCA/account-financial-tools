# -*- coding: utf-8 -*-
try:
    from . import models
    from . import wizard
    from . import report
except ImportError:
    import logging
    logging.getLogger(__name__).warn(
        "report_xlsx_helper not available in addons path")
