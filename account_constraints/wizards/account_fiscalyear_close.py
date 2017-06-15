# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models


class AccountFiscalyearCloseWizard(models.TransientModel):
    _inherit = 'account.fiscalyear.close'

    @api.multi
    def data_save(self):
        super(AccountFiscalyearCloseWizard, self).with_context(
            from_parent_object=True
        ).data_save()
