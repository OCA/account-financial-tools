# Copyright 2026 Akretion (http://www.akretion.com/)
# @author Arnaud Layec <arnaud.layec@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for line in self.line_ids:
            if message := line._check_partner_required_msg():
                raise ValidationError(message)
        return super()._post(soft=soft)
