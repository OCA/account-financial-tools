# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    posting_policy = fields.Selection(
        [('contra', 'Contra (debit<->credit)'),
         ('storno', 'Storno (-)')], default='contra',
        string='Storno or Contra', required=True,
        help="Storno allows minus postings, Refunds are posted on the "
             "same journal/account * (-1).\n"
             "Contra doesn't allow negative posting. "
             "Refunds are posted by swaping credit and debit side.")
