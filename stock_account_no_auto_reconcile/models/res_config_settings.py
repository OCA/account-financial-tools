# Copyright 2022 ForgeFlow S.L. (http://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    anglo_saxon_auto_reconcile = fields.Boolean(
        related="company_id.anglo_saxon_auto_reconcile",
        readonly=False,
        string="Reconcile Interim Accounts on the fly",
        help=(
            "Reconcile interim journal items when validating pickings or posting invoices"
        ),
    )
