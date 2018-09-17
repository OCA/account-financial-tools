# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new Joural
            with fiscal year prefix
        """
        seq_id = super(AccountJournal, self).create_sequence(vals)
        prefix = seq_id.prefix.replace('%(year)s', '%(fy)s')
        seq_id.write({'prefix': prefix})
        return seq_id
