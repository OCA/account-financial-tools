# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountAssetCompute(models.TransientModel):
    _name = 'account.asset.compute'
    _description = "Compute Assets"

    period_id = fields.Many2one(
        comodel_name='account.period', string='Period', required=True,
        domain="[('special', '=', False), ('state', '=', 'draft')]",
        default=lambda self: self._default_period_id(),
        help="Choose the period for which you want to automatically "
             "post the depreciation lines of running assets")
    note = fields.Text()

    @api.model
    def _default_period_id(self):
        ctx = dict(self._context, account_period_prefer_normal=True)
        periods = self.env['account.period'].with_context(ctx).find()
        periods = periods.filtered(lambda r: r.state == 'draft')
        if periods:
            return periods[0]
        return False

    @api.multi
    def asset_compute(self):
        assets = self.env['account.asset'].search(
            [('state', '=', 'open'), ('type', '=', 'normal')])
        created_move_ids, error_log = assets._compute_entries(
            self.period_id, check_triggers=True)

        if error_log:
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.%s_view_form_result'
                % (module, self._name))
            self.note = _("Compute Assets errors") + ':\n' + error_log
            return {
                'name': _('Compute Assets result'),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.asset.compute',
                'view_id': result_view.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
                'context': {'asset_move_ids': created_move_ids},
            }

        domain = "[('id', 'in', [" + \
            ','.join(map(str, created_move_ids)) + "])]"
        return {
            'name': _('Created Asset Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': domain,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def view_asset_moves(self):
        self.ensure_one()
        domain = [('id', 'in', self._context.get('asset_move_ids', []))]
        return {
            'name': _('Created Asset Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': domain,
            'type': 'ir.actions.act_window',
        }
