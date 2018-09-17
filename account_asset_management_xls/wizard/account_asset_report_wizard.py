# -*- coding: utf-8 -*-
# Copyright 2014 Noviat nv/sa <https://noviat.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp import ValidationError


class WizAccountAssetReport(models.TransientModel):

    _name = 'wiz.account.asset.report'
    _description = 'Financial Assets report'

    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        'Fiscal Year',
        required=True,
    )
    parent_asset_id = fields.Many2one(
        'account.asset.asset',
        'Asset Filter',
        domain=[('type', '=', 'view')],
    )

    @api.multi
    def xls_export(self):
        self.ensure_one()
        asset_obj = self.env['account.asset.asset']
        parent_asset_id = self.parent_asset_id.id
        if not parent_asset_id:
            parent_ids = asset_obj.search(
                [('type', '=', 'view'), ('parent_id', '=', False)])
            if not parent_ids:
                raise ValidationError(_(
                    "Configuration Error \nNo top level asset of type"
                    "'view' defined!"))
            else:
                parent_asset_id = parent_ids[0]

        # sanity check
        error_ids = asset_obj.search(
            [('type', '=', 'normal'), ('parent_id', '=', False)])
        for error_id in error_ids:
            error_name = error_id.name
            if error_id.code:
                error_name += ' (' + error_id.code + ')' or ''
            raise ValidationError(
                _("Configuration Error \nNo parent asset defined for asset "
                  "'%s'!") % error_name)

        domain = [('type', '=', 'normal'), ('id', 'child_of', parent_asset_id)]
        asset_ids = asset_obj.search(domain)
        if not asset_ids:
            raise ValidationError(
                _('No Data Available \nNo records found for your selection!'))

        datas = {
            'model': 'account.asset.asset',
            'fiscalyear_id': self.fiscalyear_id.id,
            'ids': [parent_asset_id],
        }
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.asset.xls',
                'datas': datas}
