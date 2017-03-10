# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    followup_line_id = fields.Many2one(
        comodel_name='account_followup.followup.line',
        string='Follow-up Level',
        ondelete='restrict',  # restrict deletion of the followup line
    )
    followup_date = fields.Date(
        string='Latest Follow-up',
        index=True,
    )
