# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, an open source suite of business apps
#    This module copyright (C) 2014-2015 Therp BV (<http://therp.nl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models
import logging


class Company(models.Model):
    _inherit = 'res.company'

    @api.one
    def reset_chart(self):
        logger = logging.getLogger('openerp.addons.account_reset_chart')

        def unlink_from_company(model):
            logger.info('Unlinking all records of model %s for company %s',
                        model, self.name)
            try:
                obj = self.env[model]
            except KeyError:
                logger.info('Model %s not found', model)
                return
            records = obj.search([('company_id', '=', self.id)])
            if records:  # account_account.unlink() breaks on empty id list
                records.unlink()

        self.env['account.journal'].search(
            [('company_id', '=', self.id)]).write({'update_posted': True})
        statements = self.env['account.bank.statement'].search(
            [('company_id', '=', self.id)])
        statements.button_cancel()
        statements.unlink()

        try:
            self.env['payment.order']
            logger.info('Deleting payment orders.')
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

        logger.info('Undoing reconciliations')
        rec_obj = self.env['account.move.reconcile']
        rec_obj.search(
            [('line_id.company_id', '=', self.id)]).unlink()

        logger.info('Reset paid invoices\'s workflows')
        paid_invoices = self.env['account.invoice'].search(
            [('company_id', '=', self.id), ('state', '=', 'paid')])
        if paid_invoices:
            self._cr.execute(
                """
                UPDATE wkf_instance
                SET state = 'active'
                WHERE res_type = 'account_invoice'
                AND res_id IN %s""" % (tuple(paid_invoices.ids),))
            self._cr.execute(
                """
                UPDATE wkf_workitem
                SET act_id = (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'account'
                        AND name = 'act_open')
                WHERE inst_id IN (
                    SELECT id FROM wkf_instance
                    WHERE res_type = 'account_invoice'
                    AND res_id IN %s)
                """ % (tuple(paid_invoices.ids),))
            paid_invoices.signal_workflow('invoice_cancel')

        logger.info('Dismantling invoices')
        inv_ids = self.env['account.invoice'].search(
            [('company_id', '=', self.id)]).ids
        if inv_ids:
            self.env['account.invoice.line'].search(
                [('invoice_id', 'in', inv_ids)]).unlink()
            self.env['account.invoice.tax'].search(
                [('invoice_id', 'in', inv_ids)]).unlink()
            logger.info('Unlinking invoices')
            self._cr.execute(
                """
                DELETE FROM account_invoice
                WHERE id IN %s""", (tuple(inv_ids),))

        logger.info('Unlinking moves')
        moves = self.env['account.move'].search([('company_id', '=', self.id)])
        if moves:
            self._cr.execute(
                """UPDATE account_move SET state = 'draft'
                   WHERE id IN %s""", (tuple(moves.ids),))
        moves.unlink()

        unlink_from_company('account.fiscal.position')
        unlink_from_company('account.tax')
        unlink_from_company('account.tax.code')
        unlink_from_company('account.journal')

        logger.info('Unlink properties with account as values')
        self._cr.execute(
            """
            DELETE FROM ir_property
            WHERE value_reference LIKE 'account.account,%%'
            AND company_id = %s""", (self.id,))
        unlink_from_company('account.account')
        return True
