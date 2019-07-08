# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AccountGroup(models.Model):
    _name = 'account.group'
    _parent_store = True
    _order = 'code_prefix'

    parent_id = fields.Many2one(
        comodel_name='account.group',
        string="Parent",
        index=True,
        ondelete='cascade',
    )
    parent_left = fields.Integer(
        string='Left Parent',
        index=True,
    )
    parent_right = fields.Integer(
        string='Right Parent',
        index=True,
    )
    name = fields.Char(
        required=True,
    )
    code_prefix = fields.Char()
    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='group_id',
        string='Accounts',
        help="Assigned accounts.",
    )
    level = fields.Integer(
        compute='_compute_level',
        store=True,
    )

    @api.depends('parent_id')
    def _compute_level(self):
        for group in self:
            level = 1
            parent = group.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            group.level = level

    def name_get(self):
        result = []
        for group in self:
            name = group.name
            if group.code_prefix:
                name = group.code_prefix + ' ' + name
            result.append((group.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        criteria_operator = (
            ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS
            else ['&', '!']
        )
        domain = criteria_operator + [
            ('code_prefix', '=ilike', name + '%'), ('name', operator, name)
        ]
        return self.search(domain + args, limit=limit).name_get()
