# -*- coding: utf-8 -*-
# © 2014-2016 Acsone SA/NV (http://www.acsone.eu)
# @author: Adrien Peiffer
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from openerp import exceptions


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.journal_id.check_chronology:
                invoices = \
                    self.search([('state', 'not in',
                                  ['open', 'paid', 'cancel', 'proforma',
                                   'proforma2']),
                                 ('date_invoice', '!=', False),
                                 ('date_invoice', '<', inv.date_invoice),
                                 ('journal_id', '=', inv.journal_id.id)],
                                limit=1)
                if len(invoices) > 0:
                    date_invoice_format = datetime\
                        .strptime(inv.date_invoice,
                                  DEFAULT_SERVER_DATE_FORMAT)
                    date_invoice_tz = fields\
                        .Date.context_today(self, date_invoice_format)
                    raise exceptions.Warning(_("Chronology Error."
                                               " Please confirm older draft"
                                               " invoices before %s and"
                                               " try again.") %
                                             date_invoice_tz)

                if inv.internal_number is False:
                    invoices = self.search([('state', 'in', ['open', 'paid']),
                                            ('date_invoice', '>',
                                             inv.date_invoice),
                                            ('journal_id', '=',
                                             inv.journal_id.id)],
                                           limit=1)
                    if len(invoices) > 0:
                        date_invoice_format = datetime\
                            .strptime(inv.date_invoice,
                                      DEFAULT_SERVER_DATE_FORMAT)
                        date_invoice_tz = fields\
                            .Date.context_today(self, date_invoice_format)
                        raise exceptions.Warning(_("Chronology Error. There"
                                                   " exist at least one"
                                                   " invoice with a date"
                                                   " posterior to %s.") %
                                                 date_invoice_tz)
        return res
