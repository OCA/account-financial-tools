# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.osv import orm


class AccountFiscalyearCloseWizard(orm.TransientModel):
    _inherit = 'account.fiscalyear.close'

    def data_save(self, cr, uid, ids, context=None):
        context = context and context.copy() or {}
        context['from_parent_object'] = True
        super(AccountFiscalyearCloseWizard, self).data_save(
            cr, uid, ids, context=context
        )
