# -*- coding: utf-8 -*-
# © 2016 Therp BV. (http://therp.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models


class AccountFiscalYear(models.Model):
    """Add option to reopen fiscal year to model."""
    _inherit = 'account.fiscalyear'

    @api.multi
    def reopen_fiscalyear(self):
        """Handle request to reopen fiscal year."""
        # Ignore if already open (= 'draft')
        self.filtered(lambda x: x.state != 'draft').write({'state': 'draft'})
