# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        previously_validated = self.filtered(lambda x: x.move_name)
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.journal_id.check_chronology:
                date_field = 'date' if inv.type in ['in_invoice', 'in_refund']\
                    else 'date_invoice'
                date_field_value = inv.date if inv.type in ['in_invoice', 'in_refund'] \
                    else inv.date_invoice
                invoices = self.search([
                    ('state', 'not in', ['open', 'paid', 'cancel', 'proforma',
                     'proforma2']),
                    (date_field, '!=', False),
                    (date_field, '<', date_field_value),
                    ('journal_id', '=', inv.journal_id.id)
                ], limit=1)
                if invoices:
                    raise UserError(_("Chronology Error. "
                                      "Please confirm older draft "
                                      "invoices before %s and try again.")
                                    % date_field_value)
                if inv not in previously_validated:
                    invoices = self.search(
                        [('state', 'in', ['open', 'paid']),
                         (date_field, '>', date_field_value),
                         ('journal_id', '=', inv.journal_id.id)],
                        limit=1)

                    if invoices:
                        raise UserError(_("Chronology Error. "
                                          "There exist at least one invoice "
                                          "with a date posterior to %s.") %
                                        date_field_value)
        return res
