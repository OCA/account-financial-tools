# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import time
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def write(self, vals):
        # fiscalyear_lock_date can't be set to a prior date
        if 'fiscalyear_lock_to_date' in vals or 'period_lock_to_date' in vals:
            self._check_lock_to_dates(vals)
        return super(ResCompany, self).write(vals)
