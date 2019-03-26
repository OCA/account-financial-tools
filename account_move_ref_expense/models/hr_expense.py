# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    @api.multi
    def _get_account_move_by_sheet(self):
        """ account.move ref to sheet calculated from move_grouped_by_sheet """
        move_grouped_by_sheet = super()._get_account_move_by_sheet()
        for sheet_id, move in move_grouped_by_sheet.items():
            move.document_id = self.env['hr.expense.sheet'].browse(sheet_id)
        return move_grouped_by_sheet
