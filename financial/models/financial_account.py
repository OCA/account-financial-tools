# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class FinancialAccount(models.Model):
    _name = b'financial.account'
    _description = 'Financial Account'
    _parent_name = 'parent_id'
    # _parent_store = True
    # _parent_order = 'code, name'
    _rec_name = 'complete_name'
    _order = 'code, complete_name'

    code = fields.Char(
        string='Code',
        size=20,
        index=True,
        required=True,
    )
    name = fields.Char(
        string='Name',
        size=60,
        index=True,
        required=True,
    )
    parent_id = fields.Many2one(
        comodel_name='financial.account',
        string='Parent account',
        ondelete='restrict',
        index=True,
    )
    parent_left = fields.Integer(
        string='Left Parent',
        index=True,
    )
    parent_right = fields.Integer(
        string='Right Parent',
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name='financial.account',
        inverse_name='parent_id',
        string='Child Accounts',
    )
    level = fields.Integer(
        string='Level',
        compute='_compute_account',
        store=True,
        index=True,
    )
    is_reduction = fields.Boolean(
        string='Is reduction account?',
        compute='_compute_account',
        store=True,
    )
    sign = fields.Integer(
        string='Sign',
        compute='_compute_account',
        store=True,
    )
    complete_name = fields.Char(
        string='Account',
        size=500,
        compute='_compute_account',
        store=True,
    )
    type = fields.Selection(
        selection=[
            ('A', 'Analytic'),
            ('S', 'Sinthetic')
        ],
        string='Type',
        compute='_compute_account',
        store=True,
        index=True,
    )

    def _compute_level(self):
        self.ensure_one()

        level = 1
        if self.parent_id:
            level += self.parent_id._compute_level()

        return level

    def _compute_complete_name(self):
        self.ensure_one()

        name = self.name

        if self.parent_id:
            name = self.parent_id._compute_complete_name() + ' / ' + name

        return name

    @api.depends('parent_id', 'code', 'name', 'child_ids.parent_id')
    def _compute_account(self):
        for account in self:
            account.level = account._compute_level()

            if account.name and (account.name.startswith('(-)')
                                 or account.name.startswith('( - )')):
                account.is_reduction = True
                account.sign = -1
            else:
                account.is_reduction = False
                account.sign = 1

            if len(account.child_ids) > 0:
                account.type = 'S'
            else:
                account.type = 'A'

            if account.code and account.name:
                account.complete_name = account.code + ' - ' + \
                    account._compute_complete_name()

    def recreate_financial_account_tree_analysis(self):
        from .financial_account_tree_analysis import \
            SQL_SELECT_ACCOUNT_TREE_ANALYSIS
        SQL_RECREATE_FINANCIAL_ACCOUNT_TREE_ANALYSIS = '''
        delete from financial_account_tree_analysis;
        insert into financial_account_tree_analysis (id, child_account_id,
          parent_account_id, level)
        ''' + SQL_SELECT_ACCOUNT_TREE_ANALYSIS

        self.env.cr.execute(SQL_RECREATE_FINANCIAL_ACCOUNT_TREE_ANALYSIS)

    @api.model
    def create(self, vals):
        res = super(FinancialAccount, self).create(vals)

        self.recreate_financial_account_tree_analysis()

        return res

    @api.multi
    def write(self, vals):
        res = super(FinancialAccount, self).write(vals)

        self.recreate_financial_account_tree_analysis()

        return res

    @api.multi
    def unlink(self):
        res = super(FinancialAccount, self).unlink()

        self.recreate_financial_account_tree_analysis()

        return res
