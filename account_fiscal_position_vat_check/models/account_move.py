# Copyright 2013-2020 Akretion France (https://akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """Override: Post/Validate the documents.

        Ensure, the customer has VAT set if required by the fiscal position.

        :param soft: if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set
            accounting date. Nothing will be performed on those documents
            before the accounting date.
        :return: Model<account.move> the documents that have been posted
        :raise UserError: Display an error for Vat if required.
        """
        for move in self:
            if (
                move.move_type in ("out_invoice", "out_refund")
                and move.fiscal_position_id.vat_required
                and not move.commercial_partner_id.vat
            ):
                raise UserError(
                    _(
                        "You are trying to validate a customer "
                        "invoice/refund with the fiscal position '%(fp)s' "
                        "that require the customer to have a VAT number. "
                        "But the Customer '%(rp)s' "
                        "doesn't have a VAT number in Odoo. "
                        "Please add the VAT number of this Customer in Odoo "
                        "and try to validate again."
                    )
                    % {
                        "fp": move.fiscal_position_id.display_name,
                        "rp": move.commercial_partner_id.display_name,
                    }
                )
        return super()._post(soft=soft)
