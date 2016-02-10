# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning
# import openerp.addons.decimal_precision as dp
# import re
import logging
_logger = logging.getLogger(__name__)


class account_invoice(models.Model):
    _inherit = "account.invoice"

    # TODO chequear si los necesitamos
    # printed_amount_tax = fields.Float(
    #     compute="_get_taxes_and_prices",
    #     digits=dp.get_precision('Account'),
    #     string=_('Tax')
    #     )
    # printed_amount_untaxed = fields.Float(
    #     compute="_get_taxes_and_prices",
    #     digits=dp.get_precision('Account'),
    #     string=_('Subtotal')
    #     )
    # printed_tax_ids = fields.One2many(
    #     compute="_get_taxes_and_prices",
    #     comodel_name='account.invoice.tax',
    #     string=_('Tax')
    #     )
    vat_discriminated = fields.Boolean(
        'Discriminate VAT?',
        compute="get_vat_discriminated",
        help="Discriminate VAT on Invoices?",
        )
    available_journal_document_type_ids = fields.Many2many(
        'account.journal.document.type',
        compute='_get_available_journal_document_type_ids',
        string='Available Journal Document Types',
        )
    journal_document_type_id = fields.Many2one(
        'account.journal.document.type',
        'Document Type',
        readonly=True,
        ondelete='restrict',
        states={'draft': [('readonly', False)]}
        )
    # we add this fields so we can search, group and analyze by this one
    document_type_id = fields.Many2one(
        'account.document.type',
        related='journal_document_type_id.document_type_id',
        copy=False,
        readonly=True,
        store=True,
        )
    document_sequence_id = fields.Many2one(
        related='journal_document_type_id.sequence_id',
        )
    document_number = fields.Char(
        string='Document Number',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]}
        )
    vat_responsability_id = fields.Many2one(
        'account.vat.responsability',
        string='VAT Responsability',
        readonly=True,
        copy=False,
        )
    display_name = fields.Char(
        compute='_get_display_name',
        )
    next_number = fields.Integer(
        compute='_get_next_number',
        string='Next Number',
        )
    use_documents = fields.Boolean(
        related='journal_id.use_documents',
        string='Use Documents?',
        readonly=True
        )
    localization = fields.Selection(
        related='company_id.localization',
        )

    @api.multi
    @api.depends(
        'journal_id.sequence_id.number_next_actual',
        'journal_document_type_id.sequence_id.number_next_actual',
        )
    def _get_next_number(self):
        """
        show next number only for invoices without number and on draft state
        """
        for invoice in self.filtered(
                lambda x: not x.display_name and x.state == 'draft'):
            if invoice.use_documents:
                sequence = invoice.journal_document_type_id.sequence_id
            elif (
                    invoice.type in ['out_refund', 'in_refund'] and
                    invoice.journal_id.refund_sequence
                    ):
                sequence = invoice.journal_id.refund_sequence_id
            else:
                sequence = invoice.journal_id.sequence_id
            # we must check if sequence use date ranges
            if not sequence.use_date_range:
                invoice.next_number = sequence.number_next_actual
            else:
                dt = fields.Date.today()
                if self.env.context.get('ir_sequence_date'):
                    dt = self.env.context.get('ir_sequence_date')
                seq_date = self.env['ir.sequence.date_range'].search([
                    ('sequence_id', '=', sequence.id),
                    ('date_from', '<=', dt),
                    ('date_to', '>=', dt)], limit=1)
                if not seq_date:
                    seq_date = sequence._create_date_range_seq(dt)
                invoice.next_number = seq_date.number_next_actual

    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
        }
        result = []
        for inv in self:
            result.append((
                inv.id,
                "%s %s" % (
                    inv.display_name or TYPES[inv.type],
                    inv.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([
                '|', ('document_number', '=', name),
                ('number', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.one
    @api.depends(
        'journal_document_type_id',
        'company_id',
        )
    def get_vat_discriminated(self):
        vat_discriminated = False
        document_letter = self.document_type_id.document_letter_id
        invoice_vat_discrimination_default = (
            self.company_id.invoice_vat_discrimination_default)
        if (
                document_letter.vat_discriminated or
                invoice_vat_discrimination_default == 'discriminate_default'
                ):
            vat_discriminated = True
        self.vat_discriminated = vat_discriminated

    @api.model
    def get_operation_type(self, invoice_type):
        if invoice_type in ['in_invoice', 'in_refund']:
            operation_type = 'purchase'
        elif invoice_type in ['out_invoice', 'out_refund']:
            operation_type = 'sale'
        else:
            operation_type = False
        return operation_type

    @api.one
    @api.depends('journal_id', 'partner_id')
    def _get_available_journal_document_type_ids(self):
        """
        This function search for available document types regarding:
        * Journal
        * Partner
        * Company
        * Documents configuration
        If needed, we can make this funcion inheritable and customizable per
        localization
        """
        invoice_type = self.type

        journal_document_types = journal_document_type = self.env[
            'account.journal.document.type']
        if invoice_type in [
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
            operation_type = self.get_operation_type(invoice_type)

            if self.use_documents:
                # to ensure we have access rights (we must see companies,
                # letters, etc)
                letters = self.sudo().env[
                    'account.document.letter'].get_valid_document_letters(
                    self.partner_id, operation_type, self.company_id)

                domain = [
                    ('journal_id', '=', self.journal_id.id),
                    '|',
                    ('document_type_id.document_letter_id', 'in', letters),
                    ('document_type_id.document_letter_id', '=', False),
                    ]

                # If internal_type in context we try to serch specific document
                # for eg used on debit notes
                internal_type = self._context.get('internal_type', False)
                if internal_type:
                    journal_document_type = journal_document_type.search(
                        domain + [
                            ('document_type_id.internal_type',
                                '=', internal_type)], limit=1)

                # For domain, we search all documents
                journal_document_types = journal_document_types.search(domain)

                # If not specific document type found, we choose another one
                if not journal_document_type and journal_document_types:
                    journal_document_type = journal_document_types[0]

        if invoice_type == 'in_invoice':
            other_document_types = (
                self.commercial_partner_id.other_document_type_ids)

            domain = [
                ('journal_id', '=', self.journal_id.id),
                ('document_type_id',
                    'in', other_document_types.ids),
                ]
            other_journal_document_types = self.env[
                'account.journal.document.type'].search(domain)

            journal_document_types += other_journal_document_types
            # if we have some document sepecific for the partner, we choose it
            if other_journal_document_types:
                journal_document_type = other_journal_document_types[0]

        self.available_journal_document_type_ids = journal_document_types
        self.journal_document_type_id = journal_document_type

    @api.one
    @api.constrains(
        'journal_id',
        'partner_id',
        'journal_document_type_id',
        )
    def _get_document_type(self):
        """ Como los campos responsability y journal document type no los
        queremos hacer funcion porque no queremos que sus valores cambien nunca
        y como con la funcion anterior solo se almacenan solo si se crea desde
        interfaz, hacemos este hack de constraint para computarlos si no estan
        computados"""
        if (
                not self.journal_document_type_id and
                self.available_journal_document_type_ids
                ):
            self.journal_document_type_id = (
                self.available_journal_document_type_ids[0])

    @api.one
    @api.depends(
        'move_name',
        'document_number',
        'document_type_id.doc_code_prefix'
        )
    def _get_display_name(self):
        """
        If move_name then invoice has been validated, then:
        * If document number and document type, we show them
        * Else, we show move_name
        """
        if self.document_number and self.document_type_id and self.move_name:
            display_name = ("%s%s" % (
                self.document_type_id.doc_code_prefix or '',
                self.document_number))
        else:
            display_name = self.move_name
        self.display_name = display_name

    @api.multi
    def check_use_documents(self):
        """
        check invoices has document class but journal require it (we check
        all invoices, not only argentinian ones)
        """
        without_doucument_class = self.filtered(
            lambda r: (
                not r.document_type_id and r.journal_id.use_documents))
        if without_doucument_class:
            raise Warning(_(
                'Some invoices have a journal that require a document but not '
                'document type has been selected.\n'
                'Invoices ids: %s' % without_doucument_class.ids))

    @api.multi
    def action_move_create(self):
        """
        We add currency rate on move creation so it can be used by electronic
        invoice later on action_number
        """
        self.check_use_documents()
        return super(account_invoice, self).action_move_create()

    @api.multi
    def invoice_validate(self):
        """
        If journal document dont have any sequence, then document number
        must be set on the account.invoice and we use thisone
        A partir de este metodo no debería haber errores porque el modulo de
        factura electronica ya habria pedido el cae. Lo ideal sería hacer todo
        esto antes que se pida el cae pero tampoco se pueden volver a atras los
        conusmos de secuencias. TODO mejorar esa parte
        """
        # We write document_number field with next invoice number by
        # document type
        for invoice in self:
            _logger.info(
                'Setting document data on account.invoice and account.move')
            commercial_partner = self.partner_id.commercial_partner_id
            journal_document_type = invoice.journal_document_type_id
            inv_vals = {
                'vat_responsability_id': (
                    commercial_partner.vat_responsability_id.id),
                }
            if invoice.use_documents:
                if not invoice.document_number:
                    if not invoice.journal_document_type_id.sequence_id:
                        raise Warning(_(
                            'Error!. Please define sequence on the journal '
                            'related documents to this invoice or set the '
                            'document number.'))
                    document_number = (
                        journal_document_type.sequence_id.next_by_id())
                    inv_vals['document_number'] = document_number
                # for canelled invoice number that still has a document_number
                # if validated again we use old document_number
                # also use this for supplier invoices
                else:
                    document_number = invoice.document_number
                invoice.move_id.write({
                    'document_type_id': (
                        journal_document_type.document_type_id.id),
                    'document_number': document_number,
                    })
            invoice.write(inv_vals)
        res = super(account_invoice, self).invoice_validate()
        return res
