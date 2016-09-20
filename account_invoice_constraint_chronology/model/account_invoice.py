# -*- coding: utf-8 -*-
# © 2014 Adrien Peiffer @ Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def action_move_create(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_move_create(
            cr, uid, ids, context=context)
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.journal_id.check_chronology:
                date_invoice_format = datetime.strptime(
                    inv.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
                date_invoice_tz = fields.date.context_today(
                    self, cr, uid, context=context,
                    timestamp=date_invoice_format)
                invoices = self.search(cr, uid, [
                    ('state', 'not in', ['open', 'paid', 'cancel', 'proforma',
                                         'proforma2']),
                    ('date_invoice', '!=', False),
                    ('date_invoice', '<', inv.date_invoice),
                    ('journal_id', '=', inv.journal_id.id)],
                    limit=1, context=context)
                if len(invoices) > 0:
                    raise osv.except_osv(_("Chronology Error!"),
                                         _(" Please confirm older draft"
                                           " invoices before %s and"
                                           " try again.") %
                                         date_invoice_tz)

                if inv.internal_number is False:
                    invoices = self.search(cr, uid, [
                        ('state', 'in', ['open', 'paid']),
                        ('date_invoice', '>', inv.date_invoice),
                        ('journal_id', '=', inv.journal_id.id)],
                        limit=1, context=context)
                    if len(invoices) > 0:
                        raise osv.except_osv(_("Chronology Error!"),
                                             _("There exist at least one"
                                               " invoice with a date"
                                               " posterior to %s.") %
                                             date_invoice_tz)
        return res
