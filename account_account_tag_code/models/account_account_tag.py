from odoo import api, fields, models


class AccountAccountTag(models.Model):
    _inherit = "account.account.tag"

    code = fields.Char()

    @api.depends("code")
    def _compute_display_name(self):
        for tag in self:
            if tag.code:
                tag.display_name = f"[{tag.code}] {tag.name}"
            else:
                tag.display_name = tag.name
