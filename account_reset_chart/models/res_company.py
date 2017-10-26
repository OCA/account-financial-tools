# -*- coding: utf-8 -*-
# Copyright 2014-2015 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models
import logging


_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def reset_chart(self):
        """ It loops selected company records and calls _reset_chart """
        return all(r._reset_chart() for r in self)

    @api.multi
    def _reset_chart(self):
        """
        This method removes the chart of account on the company record,
        including all the related financial transactions.
        """

        self.ensure_one()

        def unlink_from_company(model):
            _logger.info('Unlinking all records of model %s for company %s',
                         model, self.name)
            try:
                obj = self.env[model].with_context(active_test=False)
            except KeyError:
                _logger.info('Model %s not found', model)
                return
            self._cr.execute(
                """
                DELETE FROM ir_property ip
                USING {table} tbl
                WHERE value_reference = '{model},' || tbl.id
                    AND tbl.company_id = %s;
                """.format(model=model, table=obj._table),
                (self.id,))
            if self._cr.rowcount:
                _logger.info(
                    "Unlinked %s properties that refer to records of type %s "
                    "that are linked to company %s",
                    self._cr.rowcount, model, self.name)
            records = obj.search([('company_id', '=', self.id)])
            if records:  # account_account.unlink() breaks on empty id list
                records.unlink()

        self.env['account.journal'].search(
            [('company_id', '=', self.id)]).write({'update_posted': True})
        statements = self.env['account.bank.statement'].search(
            [('company_id', '=', self.id)])

        for statement in statements:
            statement.button_cancel()
            statement.unlink()

        try:
            voucher_obj = self.env['account.voucher']
            _logger.info('Unlinking vouchers.')
            vouchers = voucher_obj.search(
                [('company_id', '=', self.id),
                 ('state', 'in', ('proforma', 'posted'))])
            vouchers.cancel_voucher()
            voucher_obj.search(
                [('company_id', '=', self.id)]).unlink()
        except KeyError:
            pass

        try:
            if self.env['payment.order']:
                _logger.info('Unlinking payment orders.')
                self._cr.execute(
                    """
                    DELETE FROM payment_line
                    WHERE order_id IN (
                        SELECT id FROM payment_order
                        WHERE company_id = %s);
                    """, (self.id,))
                self._cr.execute(
                    "DELETE FROM payment_order WHERE company_id = %s;",
                    (self.id,))

                unlink_from_company('payment.mode')
        except KeyError:
            pass

        unlink_from_company('account.banking.account.settings')
        unlink_from_company('res.partner.bank')

        _logger.info("Cancel payments...")
        payments = self.env['account.payment'].search([
            ('company_id', '=', self.id),
        ])
        payments.cancel()
        payments.write({'move_name': False})
        payments.unlink()

        _logger.info('Reset paid invoices\'s workflows')
        paid_invoices = self.env['account.invoice'].search(
            [('company_id', '=', self.id), ('state', '=', 'paid')])
        if paid_invoices:
            for invoice in paid_invoices:
                invoice.action_cancel()

        _logger.info("Canceling open invoices...")
        open_invoices = self.env['account.invoice'].search([
            ('state', '=', 'open'),
            ('company_id', '=', self.id)
        ])
        for invoice in open_invoices:
            invoice.action_invoice_cancel()

        _logger.info("Move canceled invoices to draft stage")
        canceled_invoices = self.env['account.invoice'].search([
            ('state', '=', 'cancel'),
            ('company_id', '=', self.id)
        ])
        for invoice in canceled_invoices:
            invoice.action_invoice_draft()
            invoice.move_name = False

        invoices = self.env['account.invoice'].search(
            [('company_id', '=', self.id)])
        if invoices:
            _logger.info('Unlinking invoices')
            for invoice in invoices:
                _logger.info('Unlinking invoice: %s[%d]: %s',
                             invoice.display_name, invoice.id,
                             invoice.state)
                invoice.invoice_line_ids.unlink()
                invoice.tax_line_ids.unlink()
                invoice.unlink()

        _logger.info('Unlinking moves')
        moves = self.env['account.move'].search([('company_id', '=', self.id)])
        if moves:
            self._cr.execute(
                """UPDATE account_move SET state = 'draft'
                   WHERE id IN %s""", (tuple(moves.ids),))
        moves.mapped('line_ids').mapped('payment_id').unlink()
        moves.unlink()

        self.env['account.fiscal.position.tax'].search(
            ['|', ('tax_src_id.company_id', '=', self.id),
             ('tax_dest_id.company_id', '=', self.id)]
        ).unlink()
        self.env['account.fiscal.position.account'].search(
            ['|', ('account_src_id.company_id', '=', self.id),
             ('account_dest_id.company_id', '=', self.id)]
        ).unlink()
        unlink_from_company('account.fiscal.position')
        unlink_from_company('account.analytic.line')
        unlink_from_company('account.tax')
        unlink_from_company('account.tax.code')
        unlink_from_company('account.journal')
        unlink_from_company('account.account')

        self.env['account.partial.reconcile'].search(
            [('company_id', '=', self.id)]
        ).unlink()

        settings_id = self.env['account.config.settings'].search(
            [('company_id', '=', self.id)]
        )
        settings_id.write({
            'has_chart_of_accounts': False,
            'expects_chart_of_accounts': True,
            'chart_template_id': False,
        })
        self.chart_template_id = False

        if settings_id:
            settings_id.execute()

        return True
