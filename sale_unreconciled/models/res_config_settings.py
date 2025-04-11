# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_reconcile_account_id = fields.Many2one(
        related="company_id.sale_reconcile_account_id", readonly=False
    )
    sale_reconcile_journal_id = fields.Many2one(
        related="company_id.sale_reconcile_journal_id", readonly=False
    )
    sale_lock_auto_reconcile = fields.Boolean(
        related="company_id.sale_lock_auto_reconcile", readonly=False
    )
    sale_reconcile_tolerance = fields.Float(
        related="company_id.sale_reconcile_tolerance", readonly=False
    )
