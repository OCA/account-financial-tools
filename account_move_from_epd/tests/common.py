# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAccountMoveFromEPDCommon(AccountTestInvoicingCommon):
    """Common setup shared by all account_move_from_epd test suites.

    Provides:
    - cls.journal_misc      : the company's miscellaneous journal
    - cls.epd_loss_account  : EPD write-off loss account (created if absent)
    - cls.payment_term_epd  : 5% EPD within 10 days, net 30
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_misc = cls.company_data["default_journal_misc"]
        # Ensure the company has EPD write-off accounts configured.
        cls.epd_loss_account = cls.company_data[
            "company"
        ].account_journal_early_pay_discount_loss_account_id
        cls.epd_gain_account = cls.company_data[
            "company"
        ].account_journal_early_pay_discount_gain_account_id

        cls.payment_term_epd = cls.env["account.payment.term"].create(
            {
                "name": "30 days, 5% EPD within 10 days",
                "early_discount": True,
                "discount_percentage": 5.0,
                "discount_days": 10,
                "line_ids": [
                    (
                        0,
                        0,
                        {"value": "percent", "value_amount": 100, "nb_days": 30},
                    )
                ],
            }
        )
        cls.invoice = cls._create_invoice(
            "out_invoice",
            [(cls.product_a, 2, 300, []), (cls.product_b, 1, 400, [])],
        )
        cls.refund = cls._create_invoice("out_refund", [(cls.product_b, 1, 200, [])])
        cls._reconcile([cls.invoice, cls.refund])

    def _create_wizard(self, invoice, journal=None, date=None):
        return self.env["account.move.from_epd.generator"].create(
            {
                "origin_move_id": invoice.id,
                "epd_move_journal_id": (journal or self.journal_misc).id,
                "epd_move_date": date or fields.Date.today(),
            }
        )

    @classmethod
    def _create_invoice(cls, move_type, lines_spec, extra_values=None, post=True):
        values = {
            "move_type": move_type,
            "partner_id": cls.partner_a.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": line_spec[0].id,
                        "quantity": line_spec[1],
                        "price_unit": line_spec[2],
                        "tax_ids": line_spec[3],
                    },
                )
                for line_spec in lines_spec
            ],
        }
        if extra_values:
            values.update(extra_values)
        invoice = cls.env["account.move"].create(values)
        if post:
            invoice.action_post()
        return invoice

    @classmethod
    def _reconcile(cls, moves_list):
        # Reconcile the credit note against the invoice's receivable/payable lines.
        rec_pay_lines = sum(*moves_list).line_ids.filtered(
            lambda li: li.account_id.account_type
            in ("asset_receivable", "liability_payable")
            and not li.reconciled
        )
        rec_pay_lines.reconcile()
