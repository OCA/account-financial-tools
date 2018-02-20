# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import _, api, models
from openerp.exceptions import ValidationError


class BlockedAccountsMixin(models.AbstractModel):
    """Inherit this for supporting blocks on accounts"""
    _name = 'blocked.accounts.mixin'
    _description = 'A model that understands about blocked accounts'

    # set this to the field(s) pointing to models which can be blocked
    _blocked_accounts_fields = []

    @api.model
    def create(self, values):
        result = super(BlockedAccountsMixin, self).create(values)
        result._assert_non_blocked(values)
        return result

    @api.multi
    def write(self, values):
        result = super(BlockedAccountsMixin, self).write(values)
        self._assert_non_blocked(values)
        return result

    @api.multi
    def _assert_non_blocked(self, values):
        fields_list = set(values) & set(self._fields) & set(
            self._blocked_accounts_fields
        )
        for this in self:
            for field in fields_list:
                if this[field].blocked:
                    raise ValidationError(
                        _('%s is blocked!') % this[field].display_name
                    )
