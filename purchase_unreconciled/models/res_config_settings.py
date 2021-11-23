# Copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_reconcile_account_id = fields.Many2one(
        related="company_id.purchase_reconcile_account_id", readonly=False
    )
    purchase_reconcile_journal_id = fields.Many2one(
        related="company_id.purchase_reconcile_journal_id", readonly=False
    )
