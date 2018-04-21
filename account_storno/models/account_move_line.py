# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, tools, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    _sql_constraints = [
        ('credit_debit2', 'CHECK (1=1)',
         'Wrong credit or debit value in accounting entry !'),
    ]

    @api.model
    def _auto_init(self):
        tools.drop_constraint(
            self._cr,
            'account_move_line',
            'account_move_line_credit_debit2')
        res = super(AccountMoveLine, self)._auto_init()
        # Drop original constraint to fit storno posting with minus.
        return res

    @api.multi
    @api.constrains('debit', 'credit')
    def _check_contra_minus(self):
        """ This is to restore credit_debit2 check functionality,
            for contra journals.
        """
        storno_lines = self.filtered(
            lambda line: line.move_id.journal_id.posting_policy == 'storno')
        contra_lines = self - storno_lines
        for line in self:
            if line.journal_id.posting_policy == 'contra':
                if line.debit + line.credit < 0.0:
                    raise ValidationError(
                        _('Wrong credit or debit value in accounting entry !'))
        super(AccountMoveLine, contra_lines)._check_contra_minus()

    @api.multi
    @api.constrains('amount_currency')
    def _check_currency_amount(self):
        storno_lines = self.filtered(
            lambda line: line.move_id.journal_id.posting_policy == 'storno')
        contra_lines = self - storno_lines
        for line in storno_lines:
            if line.amount_currency:
                if (line.amount_currency > 0.0 and line.balance > 0.0) or (
                        line.amount_currency < 0.0 and line.balance < 0.0):
                    raise ValidationError(
                        _('The amount expressed in the secondary currency must'
                          ' be positive when account is debited and negative'
                          ' when account is credited.'))
        super(AccountMoveLine, contra_lines)._check_currency_amount()
