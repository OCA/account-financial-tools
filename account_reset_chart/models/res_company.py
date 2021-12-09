# copyright (C) 2014-2015 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def reset_chart(self):
        """
        This method removes the chart of account on the company record,
        including all the related financial transactions.
        """

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

        statements = self.env['account.bank.statement'].search(
            [('company_id', '=', self.id)])
        statements.button_reopen()
        statements.unlink()

        unlink_from_company('res.partner.bank')

        _logger.info('Reset paid invoices\'s workflows')
        moves = self.env['account.move'].search(
            [('company_id', '=', self.id)])
        if moves:
            moves.button_draft()
            moves.write({'posted_before': False})
            _logger.info('Unlinking invoices')
            self.env['account.move.line'].search(
                [('move_id', 'in', moves.ids)]).unlink()
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
        return True
