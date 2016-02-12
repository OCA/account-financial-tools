# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import Warning


class AccountDocmentType(models.Model):
    _name = 'account.document.type'
    _description = 'Account Document Type'

    _get_localizations = (
            lambda self, *args, **kwargs: self.env[
                'res.company']._get_localizations(*args, **kwargs))

    localization = fields.Selection(
        _get_localizations,
        'Localization',
        help='If you set a localization here then it will be available only '
        'for companies of this localization'
        )
    name = fields.Char(
        'Name',
        )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account.document.type')
        )
    doc_code_prefix = fields.Char(
        'Document Code Prefix',
        help="Prefix for Documents Codes on Invoices and Account Moves. "
        "For eg. 'FA ' will build 'FA 0001-0000001' Document Number"
        )
    code = fields.Char(
        'Code',
        help='Code used by differents localizations',
        )
    document_letter_id = fields.Many2one(
        'account.document.letter',
        'Document Letter'
        )
    report_name = fields.Char(
        'Name on Reports',
        help='Name that will be printed in reports, for example "CREDIT NOTE"'
        )
    internal_type = fields.Selection([
        ('invoice', 'Invoices'),
        ('debit_note', 'Debit Notes'),
        ('credit_note', 'Credit Notes'),
        ('ticket', 'Ticket'),
        ('receipt_invoice', 'Receipt Invoice'),
        ('in_document', 'In Document'),
        ],
        string='Internal Type',
        help='It defines some behaviours on different places:\
        * invoice: used on sale and purchase journals. Auto selected if not\
        debit_note specified on context.\
        * debit_note: used on sale and purchase journals but with lower\
        priority than invoices.\
        * credit_note: used on sale_refund and purchase_refund journals.\
        * ticket: automatically loaded for purchase journals but only loaded\
        on sales journals if point_of_sale is fiscal_printer\
        * receipt_invoice: mean to be used as invoices but not automatically\
        loaded because it is not usually used\
        * in_document: automatically loaded for purchase journals but not \
        loaded on sales journals. Also can be selected on partners, to be \
        available it must be selected on partner.\
        ')
    active = fields.Boolean(
        'Active',
        default=True
        )

    @api.multi
    def get_document_sequence_vals(self, journal):
        self.ensure_one()
        # TODO we could improove this and add a field for templating numbering
        return {
            'name': '%s - %s' % (journal.name, self.name),
            'padding': 8,
            'prefix': self.code,
            'company_id': self.company_id.id,
            }


class AccountDocumentLetter(models.Model):
    _name = 'account.document.letter'
    _description = 'Account Document Letter'

    name = fields.Char(
        'Name',
        required=True
        )
    document_type_ids = fields.One2many(
        'account.document.type',
        'document_letter_id',
        'Document Types'
        )
    issuer_ids = fields.Many2many(
        'account.vat.responsability',
        'account_document_letter_responsability_issuer_rel',
        'document_letter_id',
        'responsability_id',
        'Issuers',
        )
    receptor_ids = fields.Many2many(
        'account.vat.responsability',
        'account_document_letter_responsability_receptor_rel',
        'document_letter_id',
        'responsability_id',
        'Receptors',
        )
    active = fields.Boolean(
        'Active',
        default=True
        )
    included_tax_group_ids = fields.Many2many(
        'account.tax.group',
        'account_document_letter_tax_group_rel',
        'document_letter_id', 'tax_group_id',
        'Included Tax Groups',
        help='For documents of this letter, include this taxes of this group '
        'on invoices amounts'
        )
    # taxes_discriminated = fields.Boolean(
    #     'Taxes Discriminated on Invoices?',
    #     help="If True, the taxes will be discriminated on invoice report.")

    _sql_constraints = [('name', 'unique(name)', 'Name must be unique!'), ]
