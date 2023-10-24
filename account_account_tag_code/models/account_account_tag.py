from odoo import fields, models


class AccountAccountTag(models.Model):
    _inherit = "account.account.tag"

    code = fields.Char()

    def name_get(self):
        res = super().name_get()
        name_mapping = dict(res)
        for tag in self:
            if tag.code:
                name_mapping[tag.id] = "[" + tag.code + "] " + name_mapping[tag.id]
        return list(name_mapping.items())
