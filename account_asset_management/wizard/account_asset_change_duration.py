# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time
from lxml import etree
from openerp import api, fields, models


class AssetModify(models.TransientModel):
    _name = 'asset.modify'
    _description = 'Modify Asset'

    name = fields.Char('Reason', required=True)
    method_number = fields.Integer(
        'Number of Depreciations/Years',
        required=True,
    )
    method_period = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ],
        'Period Length',
        help="Period length for the depreciation accounting entries",
    )
    method_end = fields.Date('Ending date')
    note = fields.Text('Notes')

    def fields_view_get(
            self,
            view_id=None,
            view_type='form',
            toolbar=False,
            submenu=False):
        asset_obj = self.env['account.asset.asset']
        result = super(AssetModify, self).fields_view_get(
            view_id,
            view_type,
            toolbar=toolbar,
            submenu=submenu)
        asset_id = self.env.context.get('active_id', False)
        active_model = self.env.context.get('active_model', '')
        if active_model == 'account.asset.asset' and asset_id:
            asset = asset_obj.browse(asset_id)
            doc = etree.XML(result['arch'])
            if asset.method_time == 'number':
                node_me = doc.xpath("//field[@name='method_end']")[0]
                node_me.set('invisible', '1')
            elif asset.method_time == 'end':
                node_mn = doc.xpath("//field[@name='method_number']")[0]
                node_mn.set('invisible', '1')
            elif asset.method_time == 'year':
                node_me = doc.xpath("//field[@name='method_end']")[0]
                node_me.set('invisible', '1')
            result['arch'] = etree.tostring(doc)
        return result

    def default_get(self, fields):
        asset_obj = self.pool.get('account.asset.asset')
        res = super(AssetModify, self).default_get(fields)
        asset_id = self.env.context.get('active_id', False)
        asset = asset_obj.browse(asset_id)
        if 'name' in fields:
            res.update({'name': asset.name})
        if 'method_number' in fields and \
                asset.method_time in ['number', 'year']:
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
        return res

    @api.multi
    def modify(self):
        """
        Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        """
        self.ensure_one()
        asset_obj = self.env['account.asset.asset']
        history_obj = self.env['account.asset.history']
        asset_id = self.env.context.get('active_id', False)
        asset = asset_obj.browse(asset_id)
        data = self
        history_vals = {
            'asset_id': asset_id,
            'name': data.name,
            'method_time': asset.method_time,
            'method_number': asset.method_number,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'user_id': self.env.uid,
            'date': time.strftime('%Y-%m-%d'),
            'note': data.note,
        }
        history_obj.create(history_vals)
        asset_vals = {
            'method_number': data.method_number,
            'method_period': data.method_period,
            'method_end': data.method_end,
        }
        asset.write(asset_vals)
        asset.compute_depreciation_board()
        return {'type': 'ir.actions.act_window_close'}
