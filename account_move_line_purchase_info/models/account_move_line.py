# Copyright 2026 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _web_read_group_groupby_formatter(self, groupby_spec, values):
        formatter = super()._web_read_group_groupby_formatter(groupby_spec, values)
        if groupby_spec != "purchase_line_id":
            return formatter

        def formatter_po_line_info(value):
            return formatter(value.with_context(po_line_info=True))

        return formatter_po_line_info
