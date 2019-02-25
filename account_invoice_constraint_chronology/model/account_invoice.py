# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _prepare_previous_invoices_domain(self, invoice):
        return [
            ('state', 'not in', ['open',
                                 'paid',
                                 'cancel',
                                 'proforma',
                                 'proforma2']),
            ('date_invoice', '!=', False),
            ('date_invoice', '<', invoice.date_invoice),
            ('journal_id', '=', invoice.journal_id.id),
        ]

    @api.model
    def _prepare_later_invoices_domain(self, invoice):
        return [
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '>', invoice.date_invoice),
            ('journal_id', '=', invoice.journal_id.id),
        ]

    @api.multi
    def action_move_create(self):
        previously_validated = self.filtered(lambda inv: inv.move_name)
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if not inv.journal_id.check_chronology:
                continue
            invoices = self.search(
                self._prepare_previous_invoices_domain(inv), limit=1)
            if invoices:
                date_invoice_format = datetime.datetime(
                    year=inv.date_invoice.year,
                    month=inv.date_invoice.month,
                    day=inv.date_invoice.day,
                )
                date_invoice_tz = format_date(
                    self.env, fields.Date.context_today(
                        self, date_invoice_format))
                raise UserError(_(
                    "Chronology Error. Please confirm older draft invoices "
                    "before {date_invoice} and try again.").format(
                    date_invoice=date_invoice_tz))
            if inv not in previously_validated:
                invoices = self.search(
                    self._prepare_later_invoices_domain(inv), limit=1)
                if invoices:
                    date_invoice_format = datetime.datetime(
                        year=inv.date_invoice.year,
                        month=inv.date_invoice.month,
                        day=inv.date_invoice.day,
                    )
                    date_invoice_tz = format_date(
                        self.env, fields.Date.context_today(
                            self, date_invoice_format))
                    raise UserError(_(
                        "Chronology Error. There exist at least one invoice "
                        "with a later date to {date_invoice}.").format(
                        date_invoice=date_invoice_tz))
        return res
