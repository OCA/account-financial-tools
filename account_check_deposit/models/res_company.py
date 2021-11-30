# © 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    check_deposit_offsetting_account = fields.Selection(
        selection=[
            ("bank_account", "Bank Account"),
            ("transfer_account", "Transfer Account"),
        ],
        string="Check Deposit Offsetting Account",
        default="bank_account",
    )
    check_deposit_transfer_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Transfer Account for Check Deposits",
        ondelete="restrict",
        copy=False,
        domain=[("reconcile", "=", True), ("deprecated", "=", False)],
    )
    check_deposit_post_move = fields.Boolean(string="Post Move for Check Deposits")
