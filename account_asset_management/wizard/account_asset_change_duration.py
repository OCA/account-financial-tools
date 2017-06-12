# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from openerp import api, fields, models


class AssetModify(models.TransientModel):
    _name = 'asset.modify'
    _description = 'Modify Asset'

    name = fields.Char(
        string='Reason', size=64, required=True)
    method_number = fields.Integer(
        string='Number of Years/Depreciations', required=True)
    method_period = fields.Selection(
        selection=[('month', 'Month'),
                   ('quarter', 'Quarter'),
                   ('year', 'Year')],
        string='Period Length',
        help="Period length for the depreciation accounting entries")
    method_end = fields.Date(string='Ending date')
    note = fields.Text(string='Notes')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(AssetModify, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        asset_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        if active_model == 'account.asset.asset' and asset_id \
                and view_type == 'form':
            asset = self.env['account.asset.asset'].browse(asset_id)
            doc = etree.XML(res['arch'])
            node_me = doc.xpath("//field[@name='method_end']")[0]
            if asset.method_time in ['year', 'number']:
                node_me.set('modifiers', '{"invisible": true}')
            elif asset.method_time == 'end':
                node_me.set('modifiers', '{"required": true}')
                node_mn = doc.xpath("//field[@name='method_number']")[0]
                node_mn.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(AssetModify, self).default_get(fields_list)
        asset_id = self._context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        if 'name' in fields_list:
            res.update({'name': asset.name})
        if 'method_number' in fields_list and \
                asset.method_time in ['number', 'year']:
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields_list:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields_list and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
        return res

    @api.multi
    def modify(self):
        """
        Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        """
        self.ensure_one()
        asset_id = self._context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)

        history_vals = {
            'asset_id': asset_id,
            'name': self.name,
            'method_time': asset.method_time,
            'method_number': asset.method_number,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'user_id': self._uid,
            'date': fields.Date.context_today(self),
            'note': self.note,
        }
        self.env['account.asset.history'].create(history_vals)

        asset_vals = {}
        if self.method_number != asset.method_number:
            asset_vals['method_number'] = self.method_number
        if self.method_period != asset.method_period:
            asset_vals['method_period'] = self.method_period
        if self.method_end != asset.method_end:
            asset_vals['method_end'] = self.method_end
        if asset_vals:
            asset.write(asset_vals)
        asset.compute_depreciation_board()
        return {'type': 'ir.actions.act_window_close'}
