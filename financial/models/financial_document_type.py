# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinancialDocumentType(models.Model):
    _name = b'financial.document.type'
    _description = 'Financial Document Type'

    name = fields.Char(
        string='Document Type',
        size=30,
        required=True,
        index=True,
    )
    account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Account',
        ondelete='restrict',
    )
    # account_move_template_2receive_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Receivable',
    #     ondelete='restrict',
    # )
    # account_move_template_2pay_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Payable',
    #     ondelete='restrict',
    # )
    # account_move_template_receipt_item_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Receipt Item',
    #     ondelete='restrict',
    # )
    # account_move_template_payment_item_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Payment Item',
    #     ondelete='restrict',
    # )
    # account_move_template_money_in_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Money In',
    #     ondelete='restrict',
    # )
    # account_move_template_money_out_id = fields.Many2one(
    #     comodel_name='financial.account.move.template',
    #     string='Account Move Template when Money Out',
    #     ondelete='restrict',
    # )
    # journal_id = fields.Many2one(
    #     comodel_name='account.journal',
    #     string='Journal',
    #     ondelete='restrict',
    # )
