# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _, api, fields, models
from openerp.exceptions import UserError


class PermanentLockDateWizard(models.TransientModel):
    _name = 'permanent.lock.date.wizard'

    lock_date = fields.Date(string="Lock Date")
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company')

    @api.multi
    def confirm_date(self):
        self.ensure_one()
        company = self.company_id
        if (company.permanent_lock_date and
                self.lock_date < company.permanent_lock_date):
            raise UserError(
                _("You cannot set the permanent lock date in the past.")
            )
        # Then check if unposted moves are present before the date
        moves = self.env['account.move'].search(
            [('company_id', '=', company.id),
             ('date', '<=', self.lock_date),
             ('state', '=', 'draft')])
        if moves:
            raise UserError(
                _("You cannot set the permanent lock date since entries are "
                  "still unposted before this date.")
            )

        company.permanent_lock_date = self.lock_date
        return {'type': 'ir.actions.act_window_close'}
