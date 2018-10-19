# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAsset(models.Model):

    _name = 'account.asset'
    _inherit = ['account.asset', 'account.asset.method.number.end.mixin']
