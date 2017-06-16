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
