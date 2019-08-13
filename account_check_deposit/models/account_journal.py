# Copyright (C) 2019-Today: GTRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    can_be_deposited = fields.Boolean(string="Can be Deposited")

    can_receive_deposit = fields.Boolean(string="Can Receive Deposit")

    deposit_debit_account_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False)]",
        string="Debit Account for Deposit")

    @api.onchange('can_be_deposited', 'default_debit_account_id')
    def _onchange_default_debit_account_id(self):
        # Prefill deposit account with debit account by default
        for journal in self.filtered(lambda x: (
                not x.deposit_debit_account_id and x.can_be_deposited)):
            journal.deposit_debit_account_id =\
                journal.default_debit_account_id.id
