# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class PermanentLockDateWizard(models.TransientModel):
    _name = 'permanent.lock.date.wizard'
    _description = 'Wizard to update the permanent lock date'

    lock_date = fields.Date(string="New Permanent Lock Date", required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True)
    current_lock_date = fields.Date(
        related='company_id.permanent_lock_date', readonly=True,
        string='Current Lock Date')

    def confirm_date(self):
        self.ensure_one()
        company = self.company_id
        if (company.permanent_lock_date and
                self.lock_date < company.permanent_lock_date):
            raise UserError(_(
                "You cannot set the new permanent lock date before the "
                "current permanent lock date."))
        # Then check if unposted moves are present before the date
        moves = self.env['account.move'].search(
            [('company_id', '=', company.id),
             ('date', '<=', self.lock_date),
             ('state', '=', 'draft')])
        if moves:
            raise UserError(_(
                "You cannot set the new permanent lock date to %s "
                "since some journal entries before that date are still "
                "unposted.") % self.lock_date)

        vals = {'permanent_lock_date': self.lock_date}
        if (
                company.period_lock_date and
                company.period_lock_date < self.lock_date):
            vals['period_lock_date'] = self.lock_date
        if (
                company.fiscalyear_lock_date and
                company.fiscalyear_lock_date < self.lock_date):
            vals['fiscalyear_lock_date'] = self.lock_date
        company.write(vals)
        return {'type': 'ir.actions.act_window_close'}
