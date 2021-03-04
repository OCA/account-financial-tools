# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    permanent_lock_date = fields.Date(
        string="Permanent Lock Date",
        related='company_id.permanent_lock_date',
        help='Non-revertible closing of accounts prior to and inclusive of '
        'this date. Use it for fiscal year locking instead of "Lock Date".')

    @api.multi
    def change_permanent_lock_date(self):
        wizard = self.env['permanent.lock.date.wizard'].create({
            'company_id': self.company_id.id
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'permanent.lock.date.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
