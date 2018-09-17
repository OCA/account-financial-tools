# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('account_move_line_search_extension'):
            args.extend(['|', ('active', '=', False), ('active', '=', True)])
        return super(ResPartner, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count)
