# Copyright 2019 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import Form, common


class TestAccountMoveLinePurchaseInfo(common.TransactionCase):
    def setUp(self):
        super(TestAccountMoveLinePurchaseInfo, self).setUp()
        self.purchase_model = self.env["purchase.order"]
        self.purchase_line_model = self.env["purchase.order.line"]
        self.product_model = self.env["product.product"]
        self.product_ctg_model = self.env["product.category"]
        self.acc_type_model = self.env["account.account.type"]
        self.account_model = self.env["account.account"]
        self.am_model = self.env["account.move"]
        self.aml_model = self.env["account.move.line"]
        self.res_users_model = self.env["res.users"]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.location_stock = self.env.ref("stock.stock_location_stock")
        self.company = self.env.ref("base.main_company")
        self.group_purchase_user = self.env.ref("purchase.group_purchase_user")
        self.group_account_invoice = self.env.ref("account.group_account_invoice")
        self.group_account_manager = self.env.ref("account.group_account_manager")

        # Create account for Goods Received Not Invoiced
        acc_type = self._create_account_type("equity", "other")
        name = "Goods Received Not Invoiced"
        code = "grni"
        self.account_grni = self._create_account(acc_type, name, code, self.company)

        # Create account for Cost of Goods Sold
        acc_type = self._create_account_type("expense", "other")
        name = "Cost of Goods Sold"
        code = "cogs"
        self.account_cogs = self._create_account(acc_type, name, code, self.company)
        # Create account for Inventory
        acc_type = self._create_account_type("asset", "other")
        name = "Inventory"
        code = "inventory"
        self.account_inventory = self._create_account(
            acc_type, name, code, self.company
        )
        # Create Product
        self.product = self._create_product()

        # Create users
        self.purchase_user = self._create_user(
            "purchase_user",
            [self.group_purchase_user, self.group_account_invoice],
            self.company,
        )
        self.account_invoice = self._create_user(
            "account_invoice", [self.group_account_invoice], self.company
        )
        self.account_manager = self._create_user(
            "account_manager", [self.group_account_manager], self.company
        )

    def _create_user(self, login, groups, company):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = self.res_users_model.with_context({"no_reset_password": True}).create(
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

    def _create_account_type(self, name, a_type):
        acc_type = self.acc_type_model.create(
            {"name": name, "type": a_type, "internal_group": name}
        )
        return acc_type

    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
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
                "property_stock_account_input_categ_id": self.account_grni.id,
                "property_stock_account_output_categ_id": self.account_cogs.id,
            }
        )
        product = self.product_model.create(
            {
                "name": "test_product",
                "categ_id": product_ctg.id,
                "type": "product",
                "standard_price": 1.0,
                "list_price": 1.0,
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
                "price_unit": 500,
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
            domain.extend([("purchase_line_id", "=", purchase_line.id)])

        balance = self._get_balance(domain)
        if purchase_line:
            self.assertEqual(
                balance,
                expected_balance,
                "Balance is not %s for Purchase Line %s."
                % (str(expected_balance), purchase_line.name),
            )

    def test_purchase_invoice(self):
        """Test that the po line moves from the purchase order to the
        account move line and to the invoice line.
        """
        purchase = self._create_purchase([(self.product, 1)])
        po_line = False
        for line in purchase.order_line:
            po_line = line
            break
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.move_lines.write({"quantity_done": 1.0})
        picking.button_validate()

        expected_balance = 1.0
        self._check_account_balance(
            self.account_inventory.id,
            purchase_line=po_line,
            expected_balance=expected_balance,
        )

        f = Form(self.am_model.with_context(default_type="in_invoice"))
        f.partner_id = purchase.partner_id
        f.purchase_id = purchase
        invoice = f.save()
        invoice._post()
        purchase.flush()

        for aml in invoice.invoice_line_ids:
            if aml.product_id == po_line.product_id and aml.move_id:
                self.assertEqual(
                    aml.purchase_line_id,
                    po_line,
                    "Purchase Order line has not been copied "
                    "from the invoice to the account move line.",
                )

    def test_name_get(self):
        purchase = self._create_purchase([(self.product, 1)])
        po_line = purchase.order_line[0]
        name_get = po_line.with_context({"po_line_info": True}).name_get()
        self.assertEqual(
            name_get,
            [
                (
                    po_line.id,
                    "[%s] %s (%s)"
                    % (po_line.order_id.name, po_line.name, po_line.order_id.state),
                )
            ],
        )
        name_get_no_ctx = po_line.name_get()
        self.assertEqual(name_get_no_ctx, [(po_line.id, po_line.name)])
