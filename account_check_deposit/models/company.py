# -*- coding: utf-8 -*-
# © 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_deposit_offsetting_account = fields.Selection([
        ('bank_account', 'Bank Account'),
        ('transfer_account', 'Transfer Account'),
        ], string='Check Deposit Offsetting Account', default='bank_account')
    check_deposit_transfer_account_id = fields.Many2one(
        'account.account', string='Transfer Account for Check Deposits',
        ondelete='restrict', copy=False,
        domain=[('reconcile', '=', True), ('deprecated', '=', False)])
