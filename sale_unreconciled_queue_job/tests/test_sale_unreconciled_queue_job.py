# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import common


class TestsaleUnreconciledQueueJob(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.so_obj = cls.env["sale.order"]
        cls.product_obj = cls.env["product.product"]
        cls.category_obj = cls.env["product.category"]
        cls.partner_obj = cls.env["res.partner"]
        cls.acc_obj = cls.env["account.account"]
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")
        assets = cls.env.ref("account.data_account_type_current_assets")
        expenses = cls.env.ref("account.data_account_type_expenses")
        equity = cls.env.ref("account.data_account_type_equity")
        revenue = cls.env.ref("account.data_account_type_other_income")
        cls.company = cls.env.ref("base.main_company")

        # Create partner:
        cls.partner = cls.partner_obj.create({"name": "Test Vendor"})
        # Create standard product:
        cls.product = cls.product_obj.create(
            {"name": "Sold Product", "type": "product"}
        )
        # Create product that uses a reconcilable stock input account.
        cls.stock_journal = cls.env["account.journal"].create(
            {"name": "Stock Journal", "code": "STJTEST", "type": "general"}
        )
        cls.sale_journal = cls.env["account.journal"].create(
            {"name": "Sales Journal", "code": "SLTEST", "type": "sale"}
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
        cls.writeoff_acc = cls.acc_obj.create(
            {
                "name": "Write-offf account",
                "code": 8888,
                "user_type_id": expenses.id,
                "reconcile": True,
            }
        )
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
                "name": "sold Product (To reconcile)",
                "type": "product",
                "standard_price": 100,
                "valuation": "real_time",
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
        cls.account_revenue2 = cls.acc_obj.create(
            {
                "name": "Test revenue account 2",
                "code": 1017,
                "user_type_id": revenue.id,
                "reconcile": False,
                "company_id": cls.company.id,
            }
        )
        cls.account_expense2 = cls.acc_obj.create(
            {
                "name": "Dummy acccount",
                "code": 7991,
                "user_type_id": expenses.id,
                "reconcile": False,
                "company_id": cls.company.id,
            }
        )
        # company settings for automated valuation
        cls.company.sale_lock_auto_reconcile = True
        cls.company.sale_reconcile_account_id = cls.writeoff_acc
        cls.company.sale_reconcile_journal_id = cls.sale_journal

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

    def _create_sale(self, line_products):
        """Create a sale order.

        ``line_products`` is a list of tuple [(product, qty)]
        """
        lines = []
        for product, qty in line_products:
            line_values = {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "price_unit": 500,
            }
            lines.append((0, 0, line_values))
        return self.so_obj.create({"partner_id": self.partner.id, "order_line": lines})

    def _do_picking(self, picking, date):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        for ml in picking.move_lines:
            ml.quantity_done = ml.product_uom_qty
            ml.date = date
        picking._action_done()

    def test_00_action_reconcile(self):
        """Test only one job is created"""
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.company_id.sale_reconcile_account_id = self.writeoff_acc
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        so._create_invoices()
        # no reconciliation job
        self.assertFalse(so.reconcile_job_pending)
        QueueJob = self.env["queue.job"]
        job_task = "sale.order(%s,).action_reconcile()" % so.id
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 0)
        so.action_reconcile()
        # just one reconciliation job
        so._compute_reconcile_job_pending()
        self.assertTrue(so.reconcile_job_pending)
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 1)
        # no matter if I try to call the same method again
        so.action_reconcile()
        nb_jobs = QueueJob.search_count([("func_string", "=", job_task)])
        self.assertEqual(nb_jobs, 1)
