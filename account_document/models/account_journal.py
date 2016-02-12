# -*- coding: utf-8 -*-
from openerp import fields, models, api
# from openerp.exceptions import Warning


class AccountJournalDocumentType(models.Model):
    _name = "account.journal.document.type"
    _description = "Journal Document Types Mapping"
    _rec_name = 'document_type_id'
    _order = 'journal_id desc, sequence, id'

    document_type_id = fields.Many2one(
        'account.document.type',
        'Document Type',
        required=True,
        ondelete='cascade',
        )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Entry Sequence',
        help="This field contains the information related to the numbering of "
        "the documents entries of this document type."
        )
    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        required=True,
        ondelete='cascade',
        )
    journal_type = fields.Selection(
        related='journal_id.type',
        readonly=True,
        )
    sequence = fields.Integer(
        'Sequence',
        )


class AccountJournal(models.Model):
    _inherit = "account.journal"

    localization = fields.Selection(
        related='company_id.localization'
        )
    journal_document_type_ids = fields.One2many(
        'account.journal.document.type',
        'journal_id',
        'Documents Types',
        )
    use_documents = fields.Boolean(
        'Use Documents?'
        )
    document_sequence_type = fields.Selection(
        [('own_sequence', 'Own Sequence'),
            ('same_sequence', 'Same Invoice Sequence')],
        string='Document Sequence Type',
        default='own_sequence',
        required=True,
        help="Use own sequence or invoice sequence on Debit and Credit Notes?"
        )

    @api.onchange('company_id', 'type')
    def change_company(self):
        if self.type != 'sale' and self.company_id.localization:
            self.use_documents = True
        else:
            self.use_documents = False

    @api.multi
    @api.constrains(
        'code',
        'company_id',
        'use_documents',
        )
    def update_journal_document_types(self):
        """
        Tricky constraint to create documents on journal.
        Function to be inherited by different localizations
        """
        return True
