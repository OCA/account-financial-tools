# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def _get_open_move_lines_ids(self):
        self.ensure_one()
        return self.mapped("move_id.line_ids").filtered(
            lambda l: l.account_id == self.account_id and not l.reconciled
        ).ids
