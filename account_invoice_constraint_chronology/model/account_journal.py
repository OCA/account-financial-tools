# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    check_chronology = fields.Boolean()

    @api.onchange("type")
    def _onchange_type(self):
        super()._onchange_type()
        if self.type not in ["sale", "purchase"]:
            self.check_chronology = False
