# -*- coding: utf-8 -*-
# Copyright 2014 Camptocamp SA, 2017 ACSONE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
try:
    from odoo.addons.queue_job.job \
        import job, Job
except (ImportError, IOError) as err:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.debug(err)
else:
    from . import models
    from . import wizard
