# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    days_discount = fields.Integer('Days for discount')

    percent_discount = fields.Float('Discount percentage')

    def calc_discount_date(self, date_ref=False):
        """Calculate last date the invoice is eligible for discounts."""
        self.ensure_one()
        if not self.days_discount:
            return False
        next_date = date_ref or fields.Date.today()
        next_date += relativedelta(days=self.days_discount)
        return next_date

    def write(self, values):
        """Forbid the change of discount fields if a move was posted"""
        for term in self:
            if (
                'days_discount' in values
                and values['days_discount'] != term.days_discount
            ) or (
                'percent_discount' in values
                and values['percent_discount'] != term.percent_discount
            ):
                rec_count = self.env["account.move"].search_count(
                    [
                        ('invoice_payment_term_id', '=', term.id),
                        ('state', '=', 'posted'),
                    ]
                )
                if rec_count > 0:
                    raise UserError(
                        _(
                            'You cannot change the discount on payment term %s since some posted journal entries already exist'
                        )
                        % term.name
                    )
