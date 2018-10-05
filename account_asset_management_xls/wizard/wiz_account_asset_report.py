# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizAccountAssetReport(models.TransientModel):

    _name = 'wiz.account.asset.report'
    _description = 'Financial Assets report'

    # TODO: add support for all date range types
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Fiscal Year',
        domain=[('type_id.fiscal_year', '=', True)],
        required=True)
    parent_asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset Filter', domain=[('type', '=', 'view')])

    @api.multi
    def xls_export(self):
        self.ensure_one()
        asset_obj = self.env['account.asset']
        parent_asset = self.parent_asset_id
        if not parent_asset:
            parents = asset_obj.search(
                [('type', '=', 'view'), ('parent_id', '=', False)])
            if not parents:
                raise UserError(
                    _("Configuration Error."
                      "\nNo top level asset of type 'view' defined!"))
            self.parent_asset_id = parents[0]

        # sanity check
        errors = asset_obj.search(
            [('type', '=', 'normal'), ('parent_id', '=', False)])
        for err in errors:
            error_name = err.name
            if err.code:
                error_name += ' (' + err.code + ')' or ''
            raise UserError(
                _("Configuration Error"
                  "\nNo parent asset defined for asset '%s'!") % error_name)

        domain = [('type', '=', 'normal'),
                  ('id', 'child_of', self.parent_asset_id.id)]
        assets = asset_obj.search(domain)
        if not assets:
            raise UserError(
                _('No records found for your selection!'))

        report = {
            'type': 'ir.actions.report.xml',
            'report_type': 'xlsx',
            'report_name': 'account.asset.xlsx',
            'context': dict(self._context, xlsx_export=True),
            'datas': {'ids': [self.id]},
        }
        return report
