# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class account_invoice(models.Model):
    _inherit = "account.invoice"

    already_validated = fields.Boolean(readonly=True, copy=False)

    @api.multi
    def action_move_create(self):
        res = super(account_invoice, self).action_move_create()
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
                    date_invoice_format = fields.Date.\
                        from_string(inv.date_invoice)
                    date_invoice_tz = fields\
                        .Date.context_today(self, date_invoice_format)
                    raise UserError(_("Chronology Error. "
                                      "Please confirm older draft "
                                      "invoices before %s and try again.")
                                    % date_invoice_tz)
                if not inv.already_validated:
                    invoices = self.search([('state', 'in', ['open', 'paid']),
                                            ('date_invoice', '>',
                                             inv.date_invoice),
                                            ('journal_id', '=',
                                             inv.journal_id.id)],
                                           limit=1)

                    if len(invoices) > 0:
                        date_invoice_format = fields.Date.\
                            from_string(inv.date_invoice)
                        date_invoice_tz = fields\
                            .Date.context_today(self, date_invoice_format)
                        raise UserError(_("Chronology Error. "
                                          "There exist at least one invoice "
                                          "with a date posterior to %s.") %
                                        date_invoice_tz)
            if not inv.already_validated:
                inv.already_validated = True
        return res
