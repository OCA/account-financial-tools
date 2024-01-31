# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import fields
from odoo.tests.common import Form, SingleTransactionCase


class TestPurchaseUnreconciledQueueJob(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.po_obj = cls.env["purchase.order"]
        cls.product_obj = cls.env["product.product"]
        cls.category_obj = cls.env["product.category"]
        cls.partner_obj = cls.env["res.partner"]
        cls.acc_obj = cls.env["account.account"]
        cls.invoice_obj = cls.env["account.move"]
        cls.company = cls.env.ref("base.main_company")
        cls.company.anglo_saxon_accounting = True
        assets = cls.env.ref("account.data_account_type_current_assets")
        expenses = cls.env.ref("account.data_account_type_expenses")
        equity = cls.env.ref("account.data_account_type_equity")
        # Create partner:
        cls.partner = cls.partner_obj.create({"name": "Test Vendor"})
        # Create product that uses a reconcilable stock input account.
        cls.account = cls.acc_obj.create(
            {
                "name": "Test stock input account",
                "code": 9999,
                "user_type_id": assets.id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.writeoff_acc = cls.acc_obj.create(
            {
                "name": "Write-offf account",
                "code": 8888,
                "user_type_id": expenses.id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.stock_journal = cls.env["account.journal"].create(
            {"name": "Stock Journal", "code": "STJTEST", "type": "general"}
        )
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        acc_type = equity
        cls.account_grni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        acc_type = expenses
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        acc_type = expenses
        cls.account_gdni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = assets
        cls.account_inventory = cls._create_account(acc_type, name, code, cls.company)
        cls.product_categ = cls.category_obj.create(
            {
                "name": "Test Category",
                "property_cost_method": "standard",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_account_expense_categ_id": cls.account_cogs.id,
                "property_stock_account_output_categ_id": cls.account_gdni.id,
                "property_valuation": "real_time",
                "property_stock_journal": cls.stock_journal.id,
            }
        )
        cls.product_to_reconcile = cls.product_obj.create(
            {
                "name": "Purchased Product (To reconcile)",
                "type": "product",
                "standard_price": 100.0,
                "categ_id": cls.product_categ.id,
            }
        )
        cls.product_to_reconcile2 = cls.product_obj.create(
            {
                "name": "Purchased Product 2 (To reconcile)",
                "type": "product",
                "standard_price": 100.0,
                "categ_id": cls.product_categ.id,
            }
        )
        # Create PO:
        cls.po = cls.po_obj.create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_to_reconcile.id,
                            "name": cls.product_to_reconcile.name,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "product_uom": cls.product_to_reconcile.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        # company settings for automated valuation
        cls.company.purchase_lock_auto_reconcile = True
        cls.company.purchase_reconcile_account_id = cls.writeoff_acc
        cls.company.purchase_reconcile_journal_id = cls.stock_journal

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile=False):
        """Create an account."""
        account = cls.acc_obj.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def _do_picking(self, picking, date):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        for ml in picking.move_lines:
            ml.quantity_done = ml.product_uom_qty
        picking._action_done()
        for move in picking.move_lines:
            move.date = date

    def test_00_action_reconcile(self):
        """Test only one job is created"""
        po = self.po
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        po.action_create_invoice()
        invoice_form = Form(
            po.invoice_ids.filtered(lambda i: i.move_type == "in_invoice")[0]
        )
        invoice_form.invoice_date = datetime.now()
        with invoice_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 99
        invoice = invoice_form.save()
        invoice.action_post()
        # no reconciliation job
        self.assertFalse(po.reconcile_job_pending)
        QueueJob = self.env["queue.job"]
        job_task = "purchase.order(%s,).action_reconcile()" % po.id
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 0)
        po.action_reconcile()
        # just one reconciliation job
        po._compute_reconcile_job_pending()
        self.assertTrue(po.reconcile_job_pending)
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 1)
        # no matter if I try to call the same method again
        po.action_reconcile()
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 1)
