# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.tests import Form, common


class TestAccountMoveLinePurchaseInfoStockLandedCost(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_model = cls.env["purchase.order"]
        cls.purchase_line_model = cls.env["purchase.order.line"]
        cls.product_model = cls.env["product.product"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.account_model = cls.env["account.account"]
        cls.am_model = cls.env["account.move"]
        cls.aml_model = cls.env["account.move.line"]
        cls.res_users_model = cls.env["res.users"]

        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.company = cls.env.ref("base.main_company")
        cls.group_purchase_user = cls.env.ref("purchase.group_purchase_user")
        cls.group_account_invoice = cls.env.ref("account.group_account_invoice")
        cls.group_account_manager = cls.env.ref("account.group_account_manager")

        # Create account for Goods Received Not Invoiced
        acc_type = "equity"
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account(cls, acc_type, name, code, cls.company)

        # Create account for Cost of Goods Sold
        acc_type = "expense"
        name = "Cost of Goods Sold"
        code = "cogs"
        cls.account_cogs = cls._create_account(cls, acc_type, name, code, cls.company)
        # Create account for Inventory
        acc_type = "asset_current"
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            cls, acc_type, name, code, cls.company
        )
        # Create Product
        cls.product = cls._create_product(cls)
        cls.landed_cost_product = cls.env["product.product"].create(
            {"name": "LC cost", "type": "service", "standard_price": 10.0}
        )
        cls.landed_cost_product.product_tmpl_id.landed_cost_ok = True

        # Create users
        cls.purchase_user = cls._create_user(
            cls,
            "purchase_user",
            [cls.group_purchase_user, cls.group_account_invoice],
            cls.company,
        )
        cls.account_invoice = cls._create_user(
            cls, "account_invoice", [cls.group_account_invoice], cls.company
        )
        cls.account_manager = cls._create_user(
            cls, "account_manager", [cls.group_account_manager], cls.company
        )

    def _create_user(self, login, groups, company):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = self.res_users_model.with_context(**{"no_reset_password": True}).create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user.id

    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_ids": [(6, 0, [company.id])],
                "reconcile": True,
            }
        )
        return account

    def _create_product(self):
        """Create a Product."""
        #        group_ids = [group.id for group in groups]
        product_ctg = self.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": self.account_inventory.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_account_input_categ_id": self.account_grni.id,
                "property_stock_account_output_categ_id": self.account_cogs.id,
            }
        )
        product = self.product_model.create(
            {
                "name": "test_product",
                "categ_id": product_ctg.id,
                "standard_price": 1.0,
                "list_price": 1.0,
                "is_storable": True,
            }
        )
        return product

    def _create_purchase(self, line_products):
        """Create a purchase order.

        ``line_products`` is a list of tuple [(product, qty)]
        """
        lines = []
        for product, qty in line_products:
            line_values = {
                "name": product.name,
                "product_id": product.id,
                "product_qty": qty,
                "product_uom": product.uom_id.id,
                "price_unit": 500 if product == self.product else 100,
                "date_planned": fields.datetime.now(),
            }
            lines.append((0, 0, line_values))
        return self.purchase_model.create(
            {"partner_id": self.partner1.id, "order_line": lines}
        )

    def _get_balance(self, domain):
        """
        Call read_group method and return the balance of particular account.
        """
        aml_rec = self.aml_model.read_group(
            domain, ["debit", "credit", "account_id"], ["account_id"]
        )
        if aml_rec:
            return aml_rec[0].get("debit", 0) - aml_rec[0].get("credit", 0)
        else:
            return 0.0

    def _check_account_balance(
        self, account_id, purchase_line=None, expected_balance=0.0
    ):
        """
        Check the balance of the account
        """
        domain = [("account_id", "=", account_id)]
        if purchase_line:
            domain.extend([("oca_purchase_line_id", "=", purchase_line.id)])

        balance = self._get_balance(domain)
        if purchase_line:
            self.assertEqual(
                balance,
                expected_balance,
                f"Balance is not {str(expected_balance)} for Purchase "
                f"Line {purchase_line.name}.",
            )

    def test_purchase_landed_cost(self):
        """Test the journal items in the account move for the landed costs
        contain the po line info
        """
        purchase = self._create_purchase(
            [(self.product, 1), (self.landed_cost_product, 1)]
        )
        po_line = False
        for line in purchase.order_line:
            po_line = line
            break
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.move_ids.write({"quantity": 1.0})
        picking.button_validate()

        f = Form(self.am_model.with_context(default_move_type="in_invoice"))
        f.partner_id = purchase.partner_id
        f.invoice_date = fields.Date().today()
        f.purchase_vendor_bill_id = self.env["purchase.bill.union"].browse(-purchase.id)
        invoice = f.save()
        invoice.action_post()
        purchase.flush_model()
        lc_form = Form(self.env["stock.landed.cost"])
        lc_form.picking_ids = picking
        lc_form.vendor_bill_id = invoice
        with lc_form.cost_lines.new() as cost_line:
            cost_line.product_id = self.landed_cost_product
            cost_line.price_unit = 100
        landed_cost = lc_form.save()
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()

        for aml in landed_cost.account_move_id.line_ids:
            if aml.product_id == po_line.product_id:
                self.assertEqual(
                    aml.oca_purchase_line_id,
                    po_line,
                    "Purchase Order line has not been copied "
                    "from the invoice to the account move line.",
                )
