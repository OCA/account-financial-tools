# Copyright 2021 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountBankStatement(models.Model):
    _inherit = ["account.bank.statement", "mail.thread", "mail.activity.mixin"]
    _name = "account.bank.statement"
