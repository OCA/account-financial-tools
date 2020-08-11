# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_round


class AccountReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    apply_financial_discounts = fields.Boolean(
        string="Consider financial discounts"
    )

    financial_discount_label = fields.Char(
        string="Write-off label", default="Financial discount"
    )
    financial_discount_revenue_account_id = fields.Many2one(
        'account.account',
        string='Revenue write-off account',
        related='company_id.financial_discount_revenue_account_id',
        readonly=False,
    )
    financial_discount_expense_account_id = fields.Many2one(
        'account.account',
        string='Expense write-off account',
        related='company_id.financial_discount_expense_account_id',
        readonly=False,
    )
    financial_discount_tolerance = fields.Float(
        help="Tolerance for the application of financial discounts. Use 0.05 to"
        "apply discount up to a difference of 5 cts between statement line"
        "and move lines."
    )

    @api.constrains(
        'rule_type',
        'apply_financial_discounts',
        'match_total_amount',
        'strict_match_total_amount',
        'financial_discount_label',
        'financial_discount_revenue_account_id',
        'financial_discount_expense_account_id',
        'match_same_currency',
    )
    def _check_apply_financial_discounts(self):
        """Ensure rec model is set up properly to handle financial discounts"""
        for rec in self:
            if (
                rec.rule_type != 'invoice_matching'
                or not rec.apply_financial_discounts
            ):
                continue
            errors = []
            if (
                not rec.match_total_amount
                or rec.match_total_amount_param != 100.0
            ):
                errors.append(_("Amount Matching must be set to 100%"))
            if not rec.strict_match_total_amount:
                errors.append(_("Strict amount matching must be set"))
            # FIXME: Restrict application of financial discount if currencies
            #  are different while odoo hasn't fixed their mess
            #  cf https://github.com/odoo/odoo/pull/52529#pullrequestreview-427812393
            #  N.B: multicurrency handling is still in the process to avoid
            #  having to rewrite everything once fixed upstream
            if not rec.match_same_currency:
                errors.append(_("Same currency matching must be set"))
            if not rec.financial_discount_label:
                errors.append(_("A financial discount label must be set"))
            if not rec.financial_discount_revenue_account_id:
                errors.append(
                    _(
                        "A financial discount revenue account must be set on "
                        "the company"
                    )
                )
            if not rec.financial_discount_expense_account_id:
                errors.append(
                    _(
                        "A financial discount expense account must be set on "
                        "the company"
                    )
                )
            if errors:
                msg = (
                    _(
                        "Reconciliation model %s is set to consider financial "
                        "discount. However to function properly:\n"
                    )
                    % rec.name
                )
                raise ValidationError(msg + ' - ' + '\n - '.join(errors))

    def _get_write_off_move_lines_dict(self, st_line, move_lines=None):
        """Prepare financial discount write-off"""
        if (
            self.rule_type != 'invoice_matching'
            or not self.apply_financial_discounts
        ):
            return super()._get_write_off_move_lines_dict(
                st_line, move_lines=move_lines
            )
        # Copied from odoo
        line_residual = (
            st_line.currency_id and st_line.amount_currency or st_line.amount
        )
        line_currency = (
            st_line.currency_id
            or st_line.journal_id.currency_id
            or st_line.company_id.currency_id
        )
        total_residual = (
            move_lines
            and sum(
                aml.currency_id
                and aml.amount_residual_currency
                or aml.amount_residual
                for aml in move_lines
            )
            or 0.0
        )
        balance = total_residual - line_residual

        if float_is_zero(balance, precision_rounding=line_currency.rounding):
            return []

        discount = sum(move_lines.mapped('amount_discount'))

        write_off_account = (
            self.financial_discount_expense_account_id
            if discount > 0
            else self.financial_discount_revenue_account_id
        )
        fin_disc_write_off_vals = {
            'name': self.financial_discount_label,
            'account_id': write_off_account.id,
            'debit': discount > 0 and discount or 0,
            'credit': discount < 0 and -discount or 0,
            'reconcile_model_id': self.id,
        }
        tax_discount = sum(move_lines.mapped('amount_discount_tax'))
        if not tax_discount:
            return [fin_disc_write_off_vals]
        res = []
        for line in move_lines:
            tax_line = line.discount_tax_line_id
            if not tax_line:
                continue
            tax_write_off_vals = {
                'name': tax_line.name,
                'account_id': tax_line.account_id.id,
                'debit': tax_line.credit and line.amount_discount_tax or 0,
                'credit': tax_line.debit and line.amount_discount_tax or 0,
                'reconcile_model_id': self.id,
            }
            # Deduce tax amount from fin. disc. write-off
            if fin_disc_write_off_vals.get('credit'):
                fin_disc_write_off_vals['credit'] -= line.amount_discount_tax
            if fin_disc_write_off_vals.get('debit'):
                fin_disc_write_off_vals['debit'] -= line.amount_discount_tax
            res.append(tax_write_off_vals)
        res.append(fin_disc_write_off_vals)
        return res

    def _check_rule_propositions(self, statement_line, candidates):
        """
        Consider financial discounts in the candidates for reconciliation
        (cf. usage in _apply_rules)
        """
        res = super()._check_rule_propositions(statement_line, candidates)
        if not res and self.apply_financial_discounts:
            # Reimplement odoo function but with consideration of financial
            # discount
            if not candidates:
                return False
            date = statement_line.date or fields.Date.today()
            # Match total residual amount.
            line_residual = (
                statement_line.currency_id
                and statement_line.amount_currency
                or statement_line.amount
            )
            line_currency = (
                statement_line.currency_id
                or statement_line.journal_id.currency_id
                or statement_line.company_id.currency_id
            )
            total_residual = 0.0
            for aml in candidates:
                # TODO should we handle discounts on liquidity accounts differently
                if aml['account_internal_type'] == 'liquidity':
                    partial_residual = (
                        aml['aml_currency_id']
                        and aml['aml_amount_currency']
                        or aml['aml_balance']
                    )
                else:
                    partial_residual = (
                        aml['aml_currency_id']
                        and aml['aml_amount_residual_currency']
                        or aml['aml_amount_residual']
                    )
                partial_currency = (
                    aml['aml_currency_id']
                    and self.env['res.currency'].browse(aml['aml_currency_id'])
                    or self.company_id.currency_id
                )
                if partial_currency != line_currency:
                    partial_residual = partial_currency._convert(
                        partial_residual,
                        line_currency,
                        self.company_id,
                        aml['aml_date_maturity'],
                    )
                total_residual += partial_residual
                # Here we should only consider the discount and decrease
                #  total_residual accordingly
                if (
                    aml['discount_date']
                    and fields.Date.from_string(aml['discount_date']) >= date
                    or aml['force_financial_discount']
                ):
                    partial_discount = (
                        aml['aml_currency_id']
                        and aml['discount_amount_currency']
                        or aml['discount_amount']
                    )
                    if partial_currency != line_currency:
                        partial_discount = partial_currency._convert(
                            partial_discount,
                            line_currency,
                            self.company_id,
                            statement_line.date,
                        )
                    total_residual -= partial_discount

            # If st_line + fin disc from the prop = prop amount, return True
            #  to allow the reconciliation with this prop
            balance = total_residual - line_residual
            if (
                float_is_zero(
                    balance, precision_rounding=line_currency.rounding
                )
                or float_round(
                    abs(balance), precision_rounding=line_currency.rounding
                )
                <= self.financial_discount_tolerance
            ):
                return True
        return res

    def _get_select_communication_flag(self):
        """Consider financial discount to allow reconciliation with the prop"""
        if not self.match_total_amount or not self.strict_match_total_amount:
            res = super()._get_select_communication_flag()
        else:
            res = r'''
                -- Determine a matching or not with the statement line communication using the aml.name, move.name or move.ref.
                COALESCE(
                (
                    aml.name IS NOT NULL
                    AND
                    substring(REGEXP_REPLACE(aml.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*') != ''
                    AND
                        regexp_split_to_array(substring(REGEXP_REPLACE(aml.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'),'\s+')
                        && regexp_split_to_array(substring(REGEXP_REPLACE(st_line.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                )
                OR
                    regexp_split_to_array(substring(REGEXP_REPLACE(move.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'),'\s+')
                    && regexp_split_to_array(substring(REGEXP_REPLACE(st_line.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                OR
                (
                    move.ref IS NOT NULL
                    AND
                    substring(REGEXP_REPLACE(move.ref, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*') != ''
                    AND
                        regexp_split_to_array(substring(REGEXP_REPLACE(move.ref, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'),'\s+')
                        && regexp_split_to_array(substring(REGEXP_REPLACE(st_line.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                )
                , FALSE)
                AND
                CASE
                    WHEN abs(st_line.amount) < abs(aml.balance) - abs(aml.amount_discount) THEN (abs(st_line.amount) - abs(aml.amount_discount)) / abs(aml.balance) * 100
                    WHEN abs(st_line.amount) > abs(aml.balance) + abs(aml.amount_discount) THEN (abs(aml.balance) + abs(aml.amount_discount)) / abs(st_line.amount) * 100
                    ELSE 100
                END >= {match_total_amount_param} AS communication_flag
            '''.format(
                match_total_amount_param=self.match_total_amount_param
            )
        res += r''',
            aml.amount_discount AS discount_amount,
            aml.amount_discount_currency AS discount_amount_currency,
            aml.date_discount AS discount_date,
            move.force_financial_discount AS force_financial_discount
        '''
        return res
