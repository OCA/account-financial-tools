# Copyright 2013-2019 Akretion France (https://akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):

    _inherit = "account.move"

    def action_post(self):
        self._check_fiscal_position_vat_required()
        return super().action_post()

    def _check_fiscal_position_vat_required(self):
        """Check that the customer has VAT set if required by the
        fiscal position"""
        check_types = ("out_invoice", "out_refund")
        for rec in self:
            has_error = (
                rec.type in check_types
                and rec.fiscal_position_id.vat_required
                and not rec.partner_id.vat
            )
            if has_error:
                raise UserError(
                    _(
                        "You are trying to validate a customer invoice/refund "
                        "with the fiscal position '%s' that require the customer "
                        "to have a VAT number. But the Customer '%s' doesn't have "
                        "a VAT number in Odoo. Please add the VAT number of this "
                        "Customer in Odoo and try to validate again."
                    )
                    % (rec.fiscal_position_id.name, rec.partner_id.display_name)
                )
