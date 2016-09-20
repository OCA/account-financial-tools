# -*- coding: utf-8 -*-
# © 2014 Adrien Peiffer @ Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_journal(orm.Model):
    _inherit = 'account.journal'

    _columns = {
        'check_chronology': fields.boolean('Check Chronology'),
    }

    _defaults = {
        'check_chronology': False,
    }

    def _check_chronology_constrains(self, cr, uid, ids, context=None):
        for journal in self.browse(cr, uid, ids, context=context):
            if (journal.type not in ['sale', 'purchase', 'sale_refund',
                                     'purchase_refund'] and
                    journal.check_chronology):
                return False
        return True

    def _chronology_constraint_msg(self, cr, uid, ids, context=None):
        journal = self.browse(cr, uid, ids, context=context)[0]
        return _("Configuration Error on journal '%s' because the option "
                 "'Check Chronology' can only be activated on journals "
                 "that can be selected on invoices "
                 "(i.e. Sale, Sale Refund, Purchase, Purchase Refund "
                 "journals).") % journal.name

    _constraints = [
        (_check_chronology_constrains, _chronology_constraint_msg,
         ['type', 'check_chronology']),
    ]
