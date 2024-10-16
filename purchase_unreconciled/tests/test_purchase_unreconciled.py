# Copyright 2019-21 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import exceptions, fields
from odoo.tests.common import Form, SingleTransactionCase


class TestPurchaseUnreconciled(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.po_obj = cls.env["purchase.order"]
        cls.product_obj = cls.env["product.product"]
        cls.category_obj = cls.env["product.category"]
        cls.partner_obj = cls.env["res.partner"]
        cls.acc_obj = cls.env["account.account"]
        cls.account_move_obj = cls.env["account.move"]
        cls.company = cls.env.ref("base.main_company")
        cls.company.anglo_saxon_accounting = True
        expense_type = "expense"
        equity_type = "equity"
        asset_type = "asset_current"
        # Create partner:
        cls.partner = cls.partner_obj.create({"name": "Test Vendor"})
        # Create product that uses a reconcilable stock input account.
        cls.account = cls.acc_obj.create(
            {
                "name": "Test stock input account",
                "code": 9999,
                "account_type": asset_type,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.writeoff_acc = cls.acc_obj.create(
            {
                "name": "Write-offf account",
                "code": 8888,
                "account_type": expense_type,
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
        acc_type = equity_type
        cls.account_grni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        acc_type = expense_type
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        acc_type = expense_type
        cls.account_gdni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = asset_type
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
        # Create PO's:
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
        cls.po_2 = cls.po_obj.create(
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
                "account_type": acc_type,
                "company_id": company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def _create_delivery(
        self,
        product,
        qty,
    ):
        return self.env["stock.picking"].create(
            {
                "name": self.product_to_reconcile.name,
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product_to_reconcile.name,
                            "product_id": self.product_to_reconcile.id,
                            "product_uom": self.product_to_reconcile.uom_id.id,
                            "product_uom_qty": qty,
                            "location_id": self.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _do_picking(self, picking, date):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.date = date
        picking.button_validate()

    def test_01_nothing_to_reconcile(self):
        po = self.po
        self.assertEqual(po.state, "draft")
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        self.assertTrue(po.unreconciled)
        # Invoice created and validated:
        po.action_create_invoice()
        invoice_ids = po.invoice_ids.filtered(lambda i: i.move_type == "in_invoice")
        invoice_ids.invoice_date = datetime.now()
        invoice_ids.action_post()
        self.assertEqual(po.state, "purchase")
        # odoo does it automatically
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)

    def test_03_search_unreconciled(self):
        """Test searching unreconciled PO's."""
        po = self.po_2
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        res = self.po_obj.search([("unreconciled", "=", True)])
        po._compute_unreconciled()
        self.assertIn(po, res)
        self.assertNotIn(self.po, res)
        # Test value error:
        with self.assertRaises(ValueError):
            self.po_obj.search([("unreconciled", "=", "true")])

    def test_04_action_reconcile(self):
        """Test reconcile."""
        # Invoice created and validated:
        po = self.po_2
        self.assertTrue(po.unreconciled)
        po.action_create_invoice()
        invoice_form = Form(
            po.invoice_ids.filtered(lambda i: i.move_type == "in_invoice")[0]
        )
        # v14 reconciles automatically so here we force discrepancy
        # with invoice_form.edit(0) as inv_form:
        invoice_form.invoice_date = datetime.now()
        with invoice_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 99
        invoice = invoice_form.save()
        invoice.action_post()
        self.assertTrue(po.unreconciled)
        po.action_reconcile()
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)

    def test_05_button_done_reconcile(self):
        """Test auto reconcile when locking po."""
        po = self.po_2.copy()
        po.company_id.purchase_reconcile_account_id = self.writeoff_acc
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        # Invoice created and validated:
        # Odoo reconciles automatically so here we force discrepancy
        po.action_create_invoice()
        invoice_form = Form(
            po.invoice_ids.filtered(lambda i: i.move_type == "in_invoice")[0]
        )
        invoice_form.invoice_date = datetime.now()
        with invoice_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 99
        invoice = invoice_form.save()
        invoice.action_post()
        self.assertTrue(po.unreconciled)
        # check error if raised if not write-off account
        with self.assertRaises(exceptions.ValidationError):
            self.company.purchase_reconcile_account_id = False
            po.button_done()
        # restore the write off account
        self.company.purchase_reconcile_account_id = self.writeoff_acc
        po.button_done()
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)

    def test_06_dropship_not_reconcile_sale_journal_items(self):
        """
        Create a fake dropship and lock the PO before receiving the customer
        invoice. The PO should not close the stock interim output account
        """
        # to create the fake dropship we create a delivery and attach the
        # journals to the purchase order craeted later
        self.env["stock.quant"].create(
            {
                "product_id": self.product_to_reconcile.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "quantity": 1.0,
            }
        )
        delivery = self._create_delivery(self.product_to_reconcile, 1)
        self._do_picking(delivery, fields.Datetime.now())
        # We create the PO now and receive it
        po = self.po_2.copy()
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        self.assertTrue(po.unreconciled)
        # as long stock_dropshipping is not dependency, I force the PO to be in
        # the journal items of the delivery
        delivery_name = delivery.name
        delivery_ji = self.env["account.move.line"].search(
            [("move_id.ref", "=", delivery_name)]
        )
        delivery_ji.write(
            {"purchase_line_id": po.order_line[0], "purchase_order_id": po.id}
        )
        # then I lock the po to force reconciliation
        po.button_done()
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)
        # the PO is reconciled and the stock interim deliverd account is not
        # reconciled yet
        for jii in delivery_ji:
            self.assertFalse(jii.reconciled)

    def test_07_multicompany(self):
        """
        Force the company in the vendor bill to be wrong. The system will
        write-off the journals for the shipment because those are the only ones
        with the correct company
        """
        po = self.po.copy()
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        # Invoice created and validated:
        f = Form(self.account_move_obj.with_context(default_move_type="in_invoice"))
        f.partner_id = po.partner_id
        f.invoice_date = fields.Date().today()
        f.purchase_vendor_bill_id = self.env["purchase.bill.union"].browse(-po.id)
        invoice = f.save()
        chicago_journal = self.env["account.journal"].create(
            {
                "name": "chicago",
                "code": "ref",
                "type": "purchase",
                "company_id": self.ref("stock.res_company_1"),
            }
        )
        invoice.write(
            {
                "name": "/",
            }
        )
        invoice.write(
            {
                "company_id": self.ref("stock.res_company_1"),
                "journal_id": chicago_journal.id,
            }
        )
        invoice.action_post()
        self.assertEqual(po.state, "purchase")
        # The bill is wrong so this is unreconciled
        self.assertTrue(po.unreconciled)
        po.button_done()
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)
        # we check all the journals for the po have the same company
        ji = self.env["account.move.line"].search(
            [("purchase_order_id", "=", po.id), ("move_id", "!=", invoice.id)]
        )
        self.assertEqual(po.company_id, ji.mapped("company_id"))

    def test_08_reconcile_by_product(self):
        """
        Create a write-off by product
        """
        po = self.po.copy()
        po.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_to_reconcile2.id,
                            "name": self.product_to_reconcile2.name,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "product_uom": self.product_to_reconcile.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        # Invoice created and validated:
        f = Form(self.account_move_obj.with_context(default_move_type="in_invoice"))
        f.partner_id = po.partner_id
        f.invoice_date = fields.Date().today()
        f.purchase_vendor_bill_id = self.env["purchase.bill.union"].browse(-po.id)
        invoice = f.save()
        # force discrepancies
        with f.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 99
        with f.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 99
        invoice = f.save()
        invoice._post()
        # The bill is different price so this is unreconciled
        po._compute_unreconciled()
        self.assertTrue(po.unreconciled)
        po.button_done()
        po._compute_unreconciled()
        self.assertFalse(po.unreconciled)
        # we check all the journals are balanced by product
        ji_p1 = self.env["account.move.line"].search(
            [
                ("purchase_order_id", "=", po.id),
                ("product_id", "=", self.product_to_reconcile.id),
                ("account_id", "=", self.account_grni.id),
            ]
        )
        ji_p2 = self.env["account.move.line"].search(
            [
                ("purchase_order_id", "=", po.id),
                ("product_id", "=", self.product_to_reconcile2.id),
                ("account_id", "=", self.account_grni.id),
            ]
        )
        self.assertEqual(sum(ji_p1.mapped("balance")), 0.0)
        self.assertEqual(sum(ji_p2.mapped("balance")), 0.0)
