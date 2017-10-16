# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def search(self, cr, uid, args,
               offset=0, limit=None, order=None, context=None, count=False):
        if context and 'account_move_line_search_extension' in context:
            args.extend(['|', ('active', '=', False), ('active', '=', True)])
        return super(ResPartner, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order,
            context=context, count=count)
