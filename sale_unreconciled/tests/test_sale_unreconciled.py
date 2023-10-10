# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import common


class TestsaleUnreconciled(common.SingleTransactionCase):
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
                "name": "saled Product 2 (To reconcile)",
                "type": "product",
                "standard_price": 100,
                "valuation": "real_time",
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

    def _create_incoming(
        self,
        product,
        qty,
    ):
        return self.env["stock.picking"].create(
            {
                "name": self.product_to_reconcile.name,
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product_to_reconcile.name,
                            "product_id": self.product_to_reconcile.id,
                            "product_uom": self.product_to_reconcile.uom_id.id,
                            "product_uom_qty": qty,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_id": self.env.ref(
                                "stock.stock_location_suppliers"
                            ).id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

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

    def test_01_nothing_to_reconcile(self):
        """Test nothing is reconciled if no manual action"""
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        self.assertTrue(so.unreconciled)
        so._create_invoices()
        invoice = so.invoice_ids
        invoice.action_post()
        # not reconcile until it is locked
        self.assertTrue(so.unreconciled)

    def test_02_action_reconcile(self):
        """Test reconcile."""
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.company_id.sale_reconcile_account_id = self.writeoff_acc
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        so._create_invoices()
        invoice = so.invoice_ids
        invoice.action_post()
        so.action_reconcile()
        self.assertFalse(so.unreconciled)

    def test_03_action_reconcile(self):
        """Test reconcile."""
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.company_id.sale_reconcile_account_id = self.writeoff_acc
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        so._create_invoices()
        self.assertTrue(so.unreconciled)
        so.action_done()
        so._compute_unreconciled()
        self.assertFalse(so.unreconciled)

    def test_04_sale_mrp_anglo_saxon(self):
        """Test sale order for kit, deliver and invoice and ensure
        the iterim account is balanced and COGS is hit
        """
        self.uom_unit = self.env["uom.uom"].create(
            {
                "name": "Test-Unit",
                "category_id": self.categ_unit.id,
                "factor": 1,
                "uom_type": "bigger",
                "rounding": 1.0,
            }
        )
        self.company = self.env.ref("base.main_company")
        self.company.anglo_saxon_accounting = True
        self.partner = self.partner_obj.create({"name": "Test Customer"})
        self.category = self.env.ref("product.product_category_1").copy(
            {
                "name": "Test category",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )
        account_type = self.env["account.account.type"].create(
            {"name": "RCV type", "type": "other", "internal_group": "asset"}
        )
        self.account_receiv = self.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "RCV00",
                "user_type_id": account_type.id,
                "reconcile": True,
            }
        )
        account_expense = self.env["account.account"].create(
            {
                "name": "Expense",
                "code": "EXP00",
                "user_type_id": account_type.id,
                "reconcile": True,
            }
        )
        account_output = self.env["account.account"].create(
            {
                "name": "Output",
                "code": "OUT00",
                "user_type_id": account_type.id,
                "reconcile": True,
            }
        )
        account_valuation = self.env["account.account"].create(
            {
                "name": "Valuation",
                "code": "STV00",
                "user_type_id": account_type.id,
                "reconcile": True,
            }
        )
        self.partner.property_account_receivable_id = self.account_receiv
        self.category.property_account_income_categ_id = self.account_receiv
        self.category.property_account_expense_categ_id = account_expense
        self.category.property_stock_account_input_categ_id = self.account_receiv
        self.category.property_stock_account_output_categ_id = account_output
        self.category.property_stock_valuation_account_id = account_valuation
        self.category.property_stock_journal = self.env["account.journal"].create(
            {"name": "Stock journal", "type": "sale", "code": "STK00"}
        )

        Product = self.env["product.product"]
        # for BMS finished product is kit storable
        self.finished_product = Product.create(
            {
                "name": "Finished product",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "invoice_policy": "delivery",
                "categ_id": self.category.id,
            }
        )
        self.component1 = Product.create(
            {
                "name": "Component 1",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "categ_id": self.category.id,
                "standard_price": 20,
            }
        )
        self.component2 = Product.create(
            {
                "name": "Component 2",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "categ_id": self.category.id,
                "standard_price": 10,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.component1.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "quantity": 6.0,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.component2.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "quantity": 3.0,
            }
        )
        self.bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "phantom",
            }
        )
        BomLine = self.env["mrp.bom.line"]
        BomLine.create(
            {
                "product_id": self.component1.id,
                "product_qty": 2.0,
                "bom_id": self.bom.id,
            }
        )
        BomLine.create(
            {
                "product_id": self.component2.id,
                "product_qty": 1.0,
                "bom_id": self.bom.id,
            }
        )

        # Create a SO for a specific partner for three units of the
        # finished product
        so_vals = {
            "partner_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "partner_shipping_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.finished_product.name,
                        "product_id": self.finished_product.id,
                        "product_uom_qty": 3,
                        "product_uom": self.finished_product.uom_id.id,
                        "price_unit": self.finished_product.list_price,
                    },
                )
            ],
            "pricelist_id": self.env.ref("product.list0").id,
            "company_id": self.company.id,
        }
        self.so = self.env["sale.order"].create(so_vals)
        # Validate the SO
        self.so.action_confirm()
        # Deliver the three finished products
        pick = self.so.picking_ids
        # To check the products on the picking
        self.assertEqual(
            pick.move_lines.mapped("product_id"), self.component1 | self.component2
        )
        self._do_picking(
            pick.filtered(lambda p: p.state != "done"), fields.Datetime.now()
        )
        # Create the invoice
        self.so._create_invoices()
        invoice = self.so.invoice_ids
        invoice.action_post()
        aml = invoice.line_ids
        aml_expense = aml.filtered(lambda l: l.account_id == account_expense)
        aml_output = aml.filtered(lambda l: l.account_id == account_output)
        # Check that the cost of Good Sold entries are equal to:
        # 3* (2 * 20 + 1 * 10) = 100
        self.assertEqual(
            sum(aml_expense.mapped("debit")),
            150,
            "Cost of Good Sold entry missing or mismatching",
        )
        self.assertEqual(
            sum(aml_output.mapped("credit")), 150, "GDNI missing or mismatching"
        )
        # Now checking that the stock entries for the finished product are
        # created and not the component (decide if that is desirable)
        self.assertNotEqual(
            aml.filtered(
                lambda ml: ml.product_id == self.finished_product
                and ml.account_id == account_expense
            ),
            self.env["account.move.line"],
        )
        self.assertEqual(
            aml.filtered(
                lambda ml: ml.product_id == self.component1
                and ml.account_id == account_expense
            ),
            self.env["account.move.line"],
        )

    def test_06_dropship_not_reconcile_sale_journal_items(self):
        """
        Create a fake dropship and lock the SO before receiving the customer
        invoice. The SO should not close the stock interim output account
        """
        # to create the fake dropship we create a incoming and attach the
        # journals to the sale order craeted later
        incoming = self._create_incoming(self.product_to_reconcile, 1)
        self._do_picking(incoming, fields.Datetime.now())
        # We create the SO now and receive it
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        self.assertTrue(so.unreconciled)
        # stock_dropshipping is not a dependency, forcing the SO to be in the
        # journal items of the incoming
        incoming_name = incoming.name
        incoming_ji = self.env["account.move.line"].search(
            [("move_id.ref", "=", incoming_name)]
        )
        incoming_ji.write({"sale_line_id": so.order_line[0], "sale_order_id": so.id})
        # Lock the SO to force reconciliation
        so.action_done()
        so._compute_unreconciled()
        self.assertFalse(so.unreconciled)
        # The SO is reconciled and the stock interim deliverd account is still
        # not reconciled
        for jii in incoming_ji:
            self.assertFalse(jii.reconciled)

    def test_07_multicompany(self):
        """
        Force the company in the vendor bill to be wrong. The system will
        write-off the journals for the shipment because those are the only ones
        with the correct company
        """
        so = self._create_sale([(self.product_to_reconcile, 1)])
        so.company_id.sale_reconcile_account_id = self.writeoff_acc
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        # Invoice created and validated:
        so._create_invoices()
        invoice = so.invoice_ids
        chicago_journal = self.env["account.journal"].create(
            {
                "name": "chicago",
                "code": "ref",
                "type": "sale",
                "company_id": self.ref("stock.res_company_1"),
            }
        )
        invoice.write(
            {
                "company_id": self.ref("stock.res_company_1"),
                "journal_id": chicago_journal.id,
            }
        )
        invoice.action_post()
        self.assertEqual(so.state, "sale")
        # The invoice is wrong so this is unreconciled
        self.assertTrue(so.unreconciled)
        so.action_done()
        so._compute_unreconciled()
        self.assertFalse(so.unreconciled)
        # check all the journals for the so have the same company
        ji = self.env["account.move.line"].search(
            [("sale_order_id", "=", so.id), ("move_id", "!=", invoice.id)]
        )
        self.assertEqual(so.company_id, ji.mapped("company_id"))

    def test_08_reconcile_by_product(self):
        """
        Create a write-off by product
        """
        so = self._create_sale(
            [(self.product_to_reconcile, 1), (self.product_to_reconcile2, 1)]
        )
        so.company_id.sale_reconcile_account_id = self.writeoff_acc
        so.with_context(force_confirm_sale_order=True).action_confirm()
        self._do_picking(so.picking_ids, fields.Datetime.now())
        # Do not create invoices to force discrepancy
        so.action_done()
        # Check if all the journals are balanced by product
        ji_s1 = self.env["account.move.line"].search(
            [
                ("sale_order_id", "=", so.id),
                ("product_id", "=", self.product_to_reconcile.id),
                ("account_id", "=", self.account_gdni.id),
            ]
        )
        ji_s2 = self.env["account.move.line"].search(
            [
                ("sale_order_id", "=", so.id),
                ("product_id", "=", self.product_to_reconcile2.id),
                ("account_id", "=", self.account_gdni.id),
            ]
        )
        self.assertEqual(sum(ji_s1.mapped("balance")), 0.0)
        self.assertEqual(sum(ji_s2.mapped("balance")), 0.0)
