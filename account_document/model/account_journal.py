# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import Warning


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
    def get_journal_letter(self):
        """Function to be inherited by others"""
        self.ensure_one()
        responsability = self.company_id.vat_responsability_id
        if self.type in ['sale', 'sale_refund']:
            letters = responsability.issued_letter_ids
        elif self.type in ['purchase', 'purchase_refund']:
            letters = responsability.received_letter_ids
        return letters

    @api.one
    @api.constrains(
        'code',
        'company_id',
        'use_documents',
        )
    def check_document_classes(self):
        """
        Tricky constraint to create documents on journal.
        If needed, we can make this function inheritable by the different
        localizations.
        It creates, for journal of type:
            * sale: documents of internal types 'invoice', 'debit_note',
                'credit_note' if there is a match for document letter
        TODO complete here
        """
        if not self.use_documents:
            return True

        letters = self.get_journal_letter()

        other_purchase_internal_types = ['in_document', 'ticket']

        if self.type in ['purchase', 'sale']:
            internal_types = ['invoice', 'debit_note', 'credit_note']
            # for purchase we add other documents with letter
            if self.type == 'purchase':
                internal_types += other_purchase_internal_types
        else:
            raise Warning(_('Type %s not implemented yet' % self.type))

        document_types = self.env['account.document.type'].search([
            ('internal_type', 'in', internal_types),
            '|', ('document_letter_id', 'in', letters.ids),
            ('document_letter_id', '=', False)])

        # for purchases we add in_documents and ticket whitout letters
        # TODO ver que no hace falta agregar los tickets aca porque ahora le
        # pusimos al tique generico la letra x entonces ya se agrega solo.
        # o tal vez, en vez de usar letra x, lo deberiamos motrar tambien como
        # factible por no tener letra y ser tique
        if self.type == 'purchase':
            document_types += self.env['account.document.type'].search([
                ('internal_type', 'in', other_purchase_internal_types),
                ('document_letter_id', '=', False)])

        # take out documents that already exists
        document_types = document_types - self.mapped(
                    'journal_document_type_ids.document_type_id')

        sequence = 10
        for document_type in document_types:
            sequence_id = False
            if self.type == 'sale':
                # Si es nota de debito nota de credito y same sequence,
                # no creamos la secuencia, buscamos una que exista
                if (
                        document_type.internal_type in [
                        'debit_note', 'credit_note'] and
                        self.document_sequence_type == 'same_sequence'
                        ):
                    journal_document = self.journal_document_type_ids.search([
                        ('document_type_id.document_letter_id', '=',
                            document_type.document_letter_id.id),
                        ('journal_id', '=', self.id)], limit=1)
                    sequence_id = journal_document.sequence_id.id
                else:
                    sequence_id = self.env['ir.sequence'].create(
                        document_type.get_document_sequence_vals(self)).id
            self.journal_document_type_ids.create({
                'document_type_id': document_type.id,
                'sequence_id': sequence_id,
                'journal_id': self.id,
                'sequence': sequence,
            })
            sequence += 10
