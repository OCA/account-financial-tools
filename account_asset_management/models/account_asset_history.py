# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAssetHistory(models.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _order = 'date desc'

    name = fields.Char(string='History name', size=64, index=True)
    user_id = fields.Many2one(
        comodel_name='res.users', string='User', required=True,
        default=lambda self: self.env.user)
    date = fields.Date(required=True, default=fields.Date.context_today)
    asset_id = fields.Many2one(
        comodel_name='account.asset.asset', string='Asset',
        required=True, ondelete='cascade')
    method_time = fields.Selection(
        selection=[('year', 'Number of Years'),
                   ('number', 'Number of Depreciations'),
                   ('end', 'Ending Date')],
        string='Time Method', required=True)
    method_number = fields.Integer(string='Number of Years/Depreciations')
    method_period = fields.Selection(
        selection=[('month', 'Month'),
                   ('quarter', 'Quarter'),
                   ('year', 'Year')],
        string='Period Length',
        help="Period length for the depreciation accounting entries")
    method_end = fields.Date('Ending date')
    note = fields.Text()
