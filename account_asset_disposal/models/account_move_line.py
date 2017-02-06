# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, _
from openerp.exceptions import Warning as UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def unlink(self, check=True):
        for line in self:
            if (line.asset_id.state == 'disposed' and
                    not self.env.context.get('asset_disposal_undo', False)):
                name = '%s:%s' % (line.move_id.name, line.name)
                raise UserError(
                    _("Move line '%s' is related with a disposed asset '%s'") %
                    (name, line.asset_id.name))
        return super(AccountMoveLine, self).unlink(check=check)
