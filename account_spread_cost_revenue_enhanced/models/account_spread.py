# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountSpread(models.Model):
    _inherit = "account.spread"

    create_move_type = fields.Selection(
        selection=[
            ("entry", "Journal Entry"),
            ("out_invoice", "Customer Invoice"),
            ("in_invoice", "Vendor Bill"),
            ("out_refund", "Customer Credit Note"),
            ("in_refund", "Vendor Credit Note"),
        ],
        string="Create Entry As",
        default="entry",
        required=True,
    )

    @api.constrains("invoice_id", "invoice_type")
    def _check_invoice_type(self):
        """When linked with journal entry, no check"""
        spread = self.filtered(lambda l: not l.invoice_id.move_type == "entry")
        super(AccountSpread, spread)._check_invoice_type()

    @api.constrains("create_move_type", "debit_account_id", "credit_account_id")
    def _check_entry_type(self):
        if self.filtered(
            lambda l: l.create_move_type != "entry"
            and l.debit_account_id != l.credit_account_id
        ):
            raise UserError(
                _(
                    "When choose to create move type other than journal "
                    "entry, debit/credit account must be same"
                )
            )
