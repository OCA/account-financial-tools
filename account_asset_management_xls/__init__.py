# -*- coding: utf-8 -*-
# Copyright 2014 Noviat nv/sa (www.noviat.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
try:
    from . import account_asset
    from . import wizard
    from . import report
except ImportError:
    import logging
    logging.getLogger(__name__).warn(
        "report_xls not available in addons path")
