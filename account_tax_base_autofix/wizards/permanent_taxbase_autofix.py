# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PermanentTaxBaseAutofixWizard(models.TransientModel):
    _name = 'permanent_taxbase_autofix_wizard'

    check_taxbase = fields.Boolean(string="Check tax base")
    check_sign = fields.Boolean(string="Check tax sign")


    @api.multi
    def confirm_autofix(self):
        self.ensure_one()
        move = self.env['account.move'].browse(self.env.context.get('active_ids', []))
        move.check_taxes(check_taxbase=self.check_taxbase, check_sign=self.check_sign)
        return {'type': 'ir.actions.act_window_close'}
