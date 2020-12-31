from odoo.addons.account.tests.test_reconciliation import TestReconciliation


class TestAccountReconciliationPartial(TestReconciliation):

    """Tests for Account Reconciliation Partial"""

    def __init__(self, methodName="runTest"):
        super(TestAccountReconciliationPartial, self).__init__(methodName)
        # Skip original test from inherited class
        custom_attributes = set(dir(TestAccountReconciliationPartial)) - set(
            dir(TestReconciliation)
        )
        custom_test_methods = [
            name
            for name in custom_attributes
            if name.startswith("test_") and callable(getattr(self, name))
        ]

        if methodName not in custom_test_methods:
            method = getattr(self, methodName)
            method.__dict__["__unittest_skip__"] = True
            method.__dict__[
                "__unittest_skip_why__"
            ] = "Test executed from original module"

    def setUp(self):
        super(TestAccountReconciliationPartial, self).setUp()
        self.env.ref("base.main_company").write(
            {
                "tax_exigibility": True,
                "tax_cash_basis_journal_id": self.cash_basis_journal.id,
            }
        )

    def test_reconciliation_cash_basis(self):
        # Simulates an expense made up by 2 lines
        # one is subject to a cash basis tax
        # the other is not subject to tax

        aml_obj = self.env["account.move.line"].with_context(check_move_validity=False)

        # Purchase
        purchase_move = self.env["account.move"].create(
            {"name": "purchase", "journal_id": self.purchase_journal.id}
        )

        purchase_payable_line0 = aml_obj.create(
            {
                "account_id": self.account_rsa.id,
                "credit": 1350,
                "move_id": purchase_move.id,
            }
        )
        purchase_payable_line1 = aml_obj.create(
            {
                "account_id": self.account_rsa.id,
                "credit": 450,
                "move_id": purchase_move.id,
            }
        )
        aml_obj.create(
            {
                "name": "expenseTaxed_0",
                "account_id": self.expense_account.id,
                "debit": 1000,
                "move_id": purchase_move.id,
                "tax_ids": [(4, self.tax_cash_basis.id, False)],
                "tax_exigible": False,
            }
        )
        aml_obj.create(
            {
                "name": "expenseTaxed_1",
                "account_id": self.expense_account.id,
                "debit": 300,
                "move_id": purchase_move.id,
                "tax_ids": [(4, self.tax_cash_basis.id, False)],
                "tax_exigible": False,
            }
        )
        aml_obj.create(
            {
                "name": "expenseTaxed_2",
                "account_id": self.expense_account.id,
                "debit": 200,
                "move_id": purchase_move.id,
                "tax_ids": [(4, self.tax_cash_basis.id, False)],
                "tax_exigible": False,
            }
        )
        tax_line = aml_obj.create(
            {
                "name": "TaxLine",
                "account_id": self.tax_waiting_account.id,
                "debit": 300,
                "move_id": purchase_move.id,
                "tax_line_id": self.tax_cash_basis.id,
                "tax_exigible": False,
                "tax_repartition_line_id": (
                    self.tax_cash_basis.invoice_repartition_line_ids.filtered(
                        lambda x: x.repartition_type == "tax"
                    ).id
                ),
                "tax_base_amount": 1500,
            }
        )
        purchase_move.post()

        # Payment Move
        payment_move = self.env["account.move"].create(
            {"name": "payment", "journal_id": self.bank_journal_euro.id}
        )
        payment_payable_line = aml_obj.create(
            {
                "account_id": self.account_rsa.id,
                "debit": 1800,
                "move_id": payment_move.id,
            }
        )
        aml_obj.create(
            {
                "account_id": self.account_euro.id,
                "credit": 1800,
                "move_id": payment_move.id,
            }
        )
        payment_move.post()

        to_reconcile = (
            (purchase_move + payment_move)
            .mapped("line_ids")
            .filtered(lambda l: l.account_id.internal_type == "payable")
        )
        to_reconcile.reconcile()

        apr_ids = to_reconcile.matched_debit_ids | to_reconcile.matched_credit_ids
        cash_basis_moves = self.env["account.move"].search(
            [("tax_cash_basis_rec_id", "in", apr_ids.ids)],
        )

        self.assertEqual(len(cash_basis_moves), 2, "There should be Two CABA Entries")
        self.assertTrue(cash_basis_moves.exists())

        # check reconciliation in Payable account
        self.assertTrue(purchase_payable_line0.full_reconcile_id.exists())
        self.assertEqual(
            purchase_payable_line0.full_reconcile_id.reconciled_line_ids,
            purchase_payable_line0 + purchase_payable_line1 + payment_payable_line,
        )

        cash_basis_aml_ids = cash_basis_moves.mapped("line_ids")
        # check reconciliation in the tax waiting account
        self.assertTrue(tax_line.full_reconcile_id.exists())
        self.assertEqual(
            tax_line.full_reconcile_id.reconciled_line_ids,
            cash_basis_aml_ids.filtered(
                lambda l: l.account_id == self.tax_waiting_account
            )
            + tax_line,
        )

        self.assertEqual(len(cash_basis_aml_ids), 8, "There should 8 lines not 16")

        # check amounts
        cash_basis_move1 = cash_basis_moves.filtered(lambda m: m.amount_total == 1350)
        cash_basis_move2 = cash_basis_moves.filtered(lambda m: m.amount_total == 450)

        self.assertTrue(cash_basis_move1.exists())
        self.assertTrue(cash_basis_move2.exists())

        # For first move
        move_lines = cash_basis_move1.line_ids
        base_amount_tax_lines = move_lines.filtered(
            lambda l: l.account_id == self.tax_base_amount_account
        )
        self.assertEqual(len(base_amount_tax_lines), 2, "There should be 2 lines not 6")
        self.assertAlmostEqual(sum(base_amount_tax_lines.mapped("credit")), 1125)
        self.assertAlmostEqual(sum(base_amount_tax_lines.mapped("debit")), 1125)

        self.assertAlmostEqual(
            (move_lines - base_amount_tax_lines)
            .filtered(lambda l: l.account_id == self.tax_waiting_account)
            .credit,
            225,
        )
        self.assertAlmostEqual(
            (move_lines - base_amount_tax_lines)
            .filtered(lambda l: l.account_id == self.tax_final_account)
            .debit,
            225,
        )

        # For second move
        move_lines = cash_basis_move2.line_ids
        base_amount_tax_lines = move_lines.filtered(
            lambda l: l.account_id == self.tax_base_amount_account
        )
        self.assertEqual(len(base_amount_tax_lines), 2, "There should be 2 lines not 6")
        self.assertAlmostEqual(sum(base_amount_tax_lines.mapped("credit")), 375)
        self.assertAlmostEqual(sum(base_amount_tax_lines.mapped("debit")), 375)

        self.assertAlmostEqual(
            (move_lines - base_amount_tax_lines)
            .filtered(lambda l: l.account_id == self.tax_waiting_account)
            .credit,
            75,
        )
        self.assertAlmostEqual(
            (move_lines - base_amount_tax_lines)
            .filtered(lambda l: l.account_id == self.tax_final_account)
            .debit,
            75,
        )
