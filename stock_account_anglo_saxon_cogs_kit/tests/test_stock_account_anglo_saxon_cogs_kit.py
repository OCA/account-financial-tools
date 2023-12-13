# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields
from odoo.tests import Form, common


# these tests create accounting entries, and therefore need a chart of accounts
@common.tagged("post_install", "-at_install")
class TestStockAccountAngloSaxonCogsKit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockAccountAngloSaxonCogsKit, cls).setUpClass()
        # Useful models
        cls.StockMove = cls.env["stock.move"]
        cls.UoM = cls.env["uom.uom"]
        cls.MrpProduction = cls.env["mrp.production"]
        cls.ProductCategory = cls.env["product.category"]
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")

    def test_01_sale_mrp_anglo_saxon(self):
        """Test sale order for kit, deliver and invoice and ensure
        COGS is hit
        """
        self.env.company.currency_id = self.env.ref("base.USD")
        self.uom_unit = self.UoM.create(
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
        self.partner = self.env.ref("base.res_partner_1")
        self.category = self.env.ref("product.product_category_1").copy(
            {
                "name": "Test category",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )
        account_receiv = self.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "RCV00",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        account_expense = self.env["account.account"].create(
            {
                "name": "Expense",
                "code": "EXP00",
                "account_type": "expense",
                "reconcile": True,
            }
        )
        account_input = self.env["account.account"].create(
            {
                "name": "Input",
                "code": "IN00",
                "account_type": "liability_current",
                "reconcile": True,
            }
        )
        account_output = self.env["account.account"].create(
            {
                "name": "Output",
                "code": "OUT00",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        account_valuation = self.env["account.account"].create(
            {
                "name": "Valuation",
                "code": "STV00",
                "account_type": "asset_fixed",
                "reconcile": True,
            }
        )
        self.partner.property_account_receivable_id = account_receiv
        self.category.property_stock_account_input_categ_id = account_input
        self.category.property_stock_account_output_categ_id = account_output
        self.category.property_stock_valuation_account_id = account_valuation
        self.category.property_account_expense_categ_id = account_expense
        self.category.property_stock_journal = self.env["account.journal"].create(
            {"name": "Stock journal", "type": "sale", "code": "STK00"}
        )

        Product = self.env["product.product"]
        self.finished_product = Product.create(
            {
                "name": "KIT product",
                "type": "consu",
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
        kit = self.env["mrp.bom"].create(
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
                "bom_id": kit.id,
            }
        )
        BomLine.create(
            {
                "product_id": self.component2.id,
                "product_qty": 1.0,
                "bom_id": kit.id,
            }
        )

        # Create a SO for a specific partner for three units of the
        # finished product
        so_vals = {
            "partner_id": self.partner.id,
            "date_order": fields.Datetime.now(),
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
            pick.move_line_ids.mapped("product_id"), self.component1 | self.component2
        )
        pick.action_confirm()
        pick.action_assign()
        for move in pick.move_ids:
            move.quantity_done = move.product_uom_qty
        pick.button_validate()
        # Create the invoice
        self.so._create_invoices()
        self.invoice = self.so.invoice_ids
        # Changed the invoiced quantity of the finished product to 2
        move_form = Form(self.invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.quantity = 2.0
        self.invoice = move_form.save()
        self.invoice.action_post()
        aml = self.invoice.line_ids
        aml_expense = aml.filtered(lambda l: l.account_id == account_expense)
        aml_output = aml.filtered(lambda l: l.account_id == account_output)
        # Check that the cost of Good Sold entries are equal to:
        # 2* (2 * 20 + 1 * 10) = 100
        self.assertEqual(
            sum(aml_expense.mapped("debit")),
            100,
            "Cost of Good Sold entry missing or mismatching",
        )
        self.assertEqual(
            sum(aml_output.mapped("credit")), 100, "GDNI missing or mismatching"
        )
        # Now checking that the stock entries for the finished product are
        # created and not the component
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
