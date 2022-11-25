# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountAssetCompute(models.TransientModel):
    _name = 'account.asset.compute'
    _description = "Compute Assets"
    _inherit = ['multi.step.wizard.mixin']

    name = fields.Char()
    date_end = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        help="All depreciation lines prior to this date will be automatically"
             " posted",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.asset'))
    note = fields.Text()
    action = fields.Many2one(
        comodel_name='account.asset.actions',
        string='Action',
        readonly=True
    )

    @api.model
    def _selection_state(self):
        return [
            ('start', 'Compute'),
            ('final', 'View Asset Moves'),
        ]

    def state_exit_start(self):
        self.state = 'final'
        self.asset_compute()

    @api.multi
    def asset_compute(self):
        actions_now = False
        error_log = ''
        created_move_ids = self.env['account.move']
        for record in self:
            assets = self.env['account.asset'].search(
                [('state', '=', 'open'), ('type', '=', 'normal'), ('company_id', '=', record.company_id.id)])
            if assets:
                actions_now = self.env['account.asset.actions'].create({
                    'date_action': fields.Date.today(),
                })
                record.action = actions_now
                # assets.with_delay()._server_with_delay_compute_entries(actions_now)
                for asset in assets:
                    asset._server_compute_entries()

    @api.multi
    def view_asset_moves(self):
        self.ensure_one()
        domain = [('id', 'in', self.action.asset_move_ids.ids)]
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
    def shoot_and_forget(self):
        action = self.env.ref('account_asset_management.account_asset_actions')
        if action:
            action.with_context(date_end=self.date_end).run()
        return {'return':True, 'type':'ir.actions.act_window_close' }

