# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>)
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time
from openerp import api, fields, models, _
from openerp import tools
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID


class AccountAccount(models.Model):
    _inherit = 'account.account'

    asset_category_id = fields.Many2one(
        'account.asset.category',
        'Asset Category',
        help="Default Asset Category when creating invoice lines "
             "with this account.",
    )

    @api.multi
    @api.constrains('asset_categ_id')
    def _check_asset_categ(self):
        for rec in self:
            if rec.asset_category_id and \
                    rec.asset_category_id.account_asset_id != rec:
                raise ValidationError(_(
                    "The Asset Account defined in the Asset Category "
                    "must be equal to the account."))


class AccountFiscalyear(models.Model):
    _inherit = 'account.fiscalyear'

    @api.model
    def create(self, vals):
        recompute_obj = self.env['account.asset.recompute.trigger']
        user_obj = self.env['res.users']
        recompute_vals = {
            'reason': 'creation of fiscalyear %s' % vals.get('code'),
            'company_id':
                vals.get('company_id') or
                user_obj.browse(self.env.uid).company_id.id,
            'date_trigger': time.strftime(
                tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'state': 'open',
        }
        recompute_obj.create(SUPERUSER_ID, recompute_vals)
        return super(AccountFiscalyear, self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('date_start') or vals.get('date_stop'):
                recompute_obj = self.env['account.asset.recompute.trigger']
                fy_datas = rec.read(['code', 'company_id'])
                for fy_data in fy_datas:
                    recompute_vals = {
                        'reason':
                            'duration change of fiscalyear %s' % fy_data[
                                'code'],
                        'company_id': fy_data['company_id'][0],
                        'date_trigger':
                            time.strftime(
                                tools.DEFAULT_SERVER_DATETIME_FORMAT),
                        'state': 'open',
                    }
                    recompute_obj.sudo().create(recompute_vals)
            return super(AccountFiscalyear, self).write(vals)
