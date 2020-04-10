# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    work_with_taxes = fields.Boolean("Work with taxes")

    def get_grouping_key(self, move_tax_val):
        """ Returns a string that will be used to group account.invoice.tax sharing the same properties"""
        self.ensure_one()
        return str(move_tax_val['move_line_id']) + '-' + str(move_tax_val['tax_line_id']) + '-' + str(move_tax_val['account_id']) + '-' + str(move_tax_val['analytic_account_id'])

    def get_grouping_key_contrapart(self, move_val):
        """ Returns a string that will be used to group account.invoice.tax sharing the same properties"""
        self.ensure_one()
        return str(move_val['move_line_id']) + '-' + "99999" + str(move_val['account_id']) + '-' + str(move_val['analytic_account_id'])

    def _prepare_tax_line_vals(self, line, tax):
        account_id = self.env['account.account'].browse([tax['account_id'] or line.account_id.id])
        vals = {
            'move_id': self.id,
            'move_line_id': line.id,
            'name': ("Automatic (%s) from %s (%s)" % (tax['name'], line.account_id.name, round(line.debit+line.credit, line.company_currency_id.decimal_places))),
            'tax_line_id': tax['id'],
            'quantity': 1.0,
            'manual': False,
            'tax_included': line.tax_included,
            'debit': line.debit != 0.0 and round(tax['amount'], line.company_currency_id.decimal_places) or 0.0,
            'credit': line.credit != 0.0 and round(tax['amount'], line.company_currency_id.decimal_places) or 0.0,
            'tax_base': line.debit+line.credit,
            'base': tax['base'],
            'amount_currency': line.amount_currency,
            'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
            'account_id': tax['account_id'] or line.account_id.id,
            'company_id': account_id and account_id.company_id.id,
            'analytic_tag_ids': tax['analytic'] and line.analytic_tag_ids.ids or False,
        }
        return vals

    def _prepare_contrapart_line_vals(self, contrapart, debit, credit, tax_amount, tax_included):
        if tax_included:
            tax_amount = -tax_amount
        vals = {
            'move_id': self.id,
            'move_line_id': contrapart.id,
            'contrapart': contrapart,
            'manual': True,
            'debit': debit != 0.0 and debit + tax_amount or 0.0,
            'credit': credit != 0.0 and credit + tax_amount or 0.0,
            'account_id': contrapart.account_id.id,
            'analytic_account_id': contrapart.analytic_account_id.id,
        }
        return vals

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        contrapart = []
        for line in self.line_ids:
            if not line.account_id:
                continue
            round_curr = line.company_currency_id.round
            amount = line.debit + line.credit
            if line.tax_included:
                incl_tax = line.tax_ids.filtered(lambda tax: not tax.price_include)
                amount = incl_tax.compute_all(amount)['total_excluded']
            taxes = line.tax_ids.compute_all(amount, line.company_currency_id, line.quantity or 1.0, line.product_id, line.partner_id)['taxes']
            if not taxes:
                contrapart.append(line)
                continue
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])

        # Generate contrapart
        if contrapart and tax_grouped:
            tax_amount = sum(x['debit'] + x['credit'] for x in tax_grouped.values() if not x['tax_included'])
            tax_amount_included = sum(x['debit'] + x['credit'] for x in tax_grouped.values() if x['tax_included'])
            contrapart_amount = abs(sum(x.debit + x.credit for x in contrapart))
            debit = credit = 0.0
            for line in contrapart:
                if tax_amount > 0.0 and line.debit > 0.0:
                    continue
                if tax_amount < 0.0 and line.credit > 0.0:
                    continue
                if line.debit == 0.0 and line.credit == 0.0:
                    continue
                val_contrapart = self._prepare_contrapart_line_vals(line, line.debit, line.credit, abs(line.debit+line.credit)/contrapart_amount*tax_amount, False)
                key_contrapart = self.get_grouping_key_contrapart(val_contrapart)
                tax_grouped[key_contrapart] = val_contrapart
                debit += val_contrapart['debit']
                credit += val_contrapart['credit']
            for line in contrapart:
                if tax_amount > 0.0 and line.debit > 0.0:
                    continue
                if tax_amount < 0.0 and line.credit > 0.0:
                    continue
                if line.debit == 0.0 and line.credit == 0.0:
                    continue
                val_contrapart = self._prepare_contrapart_line_vals(line, debit, credit, abs(line.debit+line.credit)/contrapart_amount*tax_amount_included, True)
                key_contrapart = self.get_grouping_key_contrapart(val_contrapart)
                tax_grouped[key_contrapart] = val_contrapart
        return tax_grouped

    @api.multi
    def compute_taxes(self):
        ctx = dict(self._context)
        ctx.update({'check_move_validity': False})
        move_line_vals = []
        debit = credit = 0.0

        for move in self:
            # Delete non-manual tax lines
            # self._cr.execute("DELETE FROM account_move_line WHERE move_id=%s AND manual is False", (move.id,))
            # if self._cr.rowcount:
            #    self.invalidate_cache()
            #    self.write({'line_ids': []})

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = move.get_taxes_values()
            # Create new movement for tax lines in cache
            with self.env.do_in_onchange():
                for tax in tax_grouped.values():
                    debit = tax['debit']
                    credit = tax['credit']
                    if debit < 0.0:
                        tax['debit'] = 0.0
                        tax['credit'] = -debit
                    if credit < 0.0:
                        tax['credit'] = 0.0
                        tax['debit'] = -credit
                    if tax.get('contrapart'):
                        contrapart = tax['contrapart']
                        del tax['contrapart']
                        del tax['move_line_id']
                        del tax['move_id']
                        contrapart.update(tax)
                    else:
                        move.line_ids.new(tax)
            # Prepare to write
            for line in move.line_ids:
                move_line_val = line._convert_to_write(line._cache)
                debit += move_line_val['debit']
                credit += move_line_val['credit']
                if line.id not in move.line_ids.ids:
                    move_line_vals.append((0, False, move_line_val))
                else:
                    move_line_vals.append((1, line.id, move_line_val))
        if move_line_vals:
            move.with_context(ctx).line_ids = move_line_vals
        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'line_ids': []})

    #@api.multi
    #def assert_balanced(self):
    #    #_logger.info("ASSERT %s" % self._context)
    #    if not self.ids:
    #        return True
    #    if self._context.get('force_uncheck'):
    #        return True
    #    return True
    #    prec = self.env['decimal.precision'].precision_get('Account')

    #    self._cr.execute("""\
    #        SELECT      move_id
    #        FROM        account_move_line
    #        WHERE       move_id in %s
    #        GROUP BY    move_id
    #        HAVING      abs(sum(debit) - sum(credit)) > %s
    #        """, (tuple(self.ids), 10 ** (-max(5, prec))))
    #    if len(self._cr.fetchall()) != 0:
    #        raise UserError(_("Cannot create unbalanced journal entry."))
    #    return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_included = fields.Boolean("Included taxes")
    manual = fields.Boolean(default=True)
    work_with_taxes = fields.Boolean(related="move_id.work_with_taxes")

    @api.onchange('account_id')
    @api.depends('tax_ids', 'manual', 'move_id.work_with_taxes')
    def _onchange_account_id(self):
        if self.account_id.tax_ids and self.move_id.work_with_taxes:
            self.tax_ids = [[6, False, list(set(self.tax_ids.ids + self.account_id.tax_ids.ids))]]

    @api.onchange('tax_ids')
    @api.depends('move_id.work_with_taxes', 'manual')
    def _onchange_tax_ids(self):
        if self.tax_line_id and self.move_id.work_with_taxes:
            self.manual = False
            self.move_id.compute_taxes()
