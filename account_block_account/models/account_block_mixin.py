# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountBlockMixin(models.AbstractModel):
    """Inherit this from models that can be blocked"""
    _name = 'account.block.mixin'
    _description = 'Mixin for accounting entities that can be blocked'

    blocked = fields.Boolean(default=False)

    @api.multi
    def name_get(self):
        return [
            (this_id, '%s%s' % (
                name, '' if not self.browse(this_id).blocked else ' [X]'
            ))
            for this_id, name in super(AccountBlockMixin, self).name_get()
        ]
