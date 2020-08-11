# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools.misc import format_date, formatLang


class ReconciliationWidget(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def _prepare_move_lines(
        self,
        move_lines,
        target_currency=False,
        target_date=False,
        recs_count=0,
    ):
        """Extend values with fin disc data to be processed/displayed by JS"""
        ml_dicts = super()._prepare_move_lines(
            move_lines,
            target_currency=target_currency,
            target_date=target_date,
            recs_count=recs_count,
        )
        index_list = move_lines.mapped('id')
        for line in ml_dicts:
            ml_obj = move_lines[index_list.index(line['id'])]
            company_currency = ml_obj.company_id.currency_id
            line_currency = (
                (ml_obj.currency_id and ml_obj.amount_currency)
                and ml_obj.currency_id
                or company_currency
            )
            amount_discount = ml_obj.amount_discount
            amount_discount_currency = ml_obj.amount_discount_currency
            disc_date = ml_obj.date_discount
            # Set a key to allow financial discount write-off creation from JS
            line['financial_discount_available'] = (
                (disc_date and target_date)
                and disc_date >= target_date
                or ml_obj.move_id.force_financial_discount
            )
            line['amount_discount'] = amount_discount
            line['amount_discount_currency'] = amount_discount_currency
            line['date_discount'] = disc_date
            line['amount_discount_tax'] = ml_obj.amount_discount_tax
            line['discount_tax_line_name'] = ml_obj.discount_tax_line_id.name
            line['discount_tax_line_account_id'] = [
                ml_obj.discount_tax_line_id.account_id.id,
                ml_obj.discount_tax_line_id.account_id.display_name,
            ]
            line['date_discount_str'] = (format_date(self.env, disc_date),)
            line['amount_discount_str'] = formatLang(
                self.env,
                abs(ml_obj.amount_discount),
                currency_obj=target_currency,
            )
            line['amount_discount_currency_str'] = (
                ml_obj.amount_discount_currency
                and formatLang(
                    self.env,
                    abs(ml_obj.amount_discount_currency),
                    currency_obj=line_currency,
                )
                or ""
            )
            line['amount_discount_tax_str'] = (
                ml_obj.amount_discount_tax
                and "%s (%s - %s)"
                % (
                    formatLang(
                        self.env,
                        abs(ml_obj.amount_discount_tax),
                        currency_obj=target_currency,
                    ),
                    ml_obj.discount_tax_line_id.account_id.display_name,
                    ml_obj.discount_tax_line_id.name,
                )
                or ""
            )
        return ml_dicts
