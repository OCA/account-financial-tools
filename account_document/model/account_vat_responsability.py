# -*- coding: utf-8 -*-
from openerp import fields, models
# from openerp.exceptions import Warning


class AccountVatResponsability(models.Model):
    _name = 'account.vat.responsability'
    _description = 'Account VAT Responsability'
    _order = 'sequence'

    name = fields.Char(
        'Name',
        size=64,
        required=True
        )
    sequence = fields.Integer(
        'Sequence',
        )
    code = fields.Char(
        'Code',
        size=8,
        required=True
        )
    active = fields.Boolean(
        'Active',
        default=True
        )
    issued_letter_ids = fields.Many2many(
        'account.document.letter',
        'account_document_letter_letter_issuer_rel',
        'responsability_id',
        'letter_id',
        'Issued Document Letters'
        )
    received_letter_ids = fields.Many2many(
        'account.document.letter',
        'account_document_letter_letter_receptor_rel',
        'responsability_id',
        'letter_id',
        'Received Document Letters'
        )
    vat_tax_required_on_sales_invoices = fields.Boolean(
        'VAT Tax Required on Sales Invoices?',
        help='If True, then a vay tax is mandatory on each sale invoice for '
        'companies of this responsability',
        )

    _sql_constraints = [('name', 'unique(name)', 'Name must be unique!'),
                        ('code', 'unique(code)', 'Code must be unique!')]
