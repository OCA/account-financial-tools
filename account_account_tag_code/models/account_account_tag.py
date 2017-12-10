# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    code = fields.Char()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                      ('code', '=ilike', name + '%'),
                      ('name', operator, name)]
            if operator in NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        tags = self.search(domain + args, limit=limit)
        return tags.name_get()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for tag in self:
            if tag.code:
                name = ' - '.join([tag.code, tag.name])
                result.append((tag.id, name))
        return result
