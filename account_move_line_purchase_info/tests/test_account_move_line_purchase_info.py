# Copyright 2021 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests import common


class TestAccountMoveLinePurchaseInfo(common.TransactionCase):
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

        cls.partner1 = cls.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "supplier_rank": 1,
            }
        )
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
        cls.location_stock.write(
            {
                "valuation_account_id": cls.account_grni.id,
            }
        )
        # Create Product
        cls.product = cls._create_product(cls)

        cls.product.categ_id.write(
            {
                "property_valuation": "real_time",
                "property_stock_valuation_account_id": cls.account_inventory.id,
            }
        )

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
                "group_ids": [(6, 0, group_ids)],
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
                "product_uom_id": product.uom_id.id,
                "price_unit": 500,
                "date_planned": fields.Datetime.now(),
            }
            lines.append((0, 0, line_values))
        return self.purchase_model.create(
            {"partner_id": self.partner1.id, "order_line": lines}
        )

    def _get_balance(self, domain):
        result = self.aml_model._read_group(
            domain=domain,
            groupby=["account_id"],
            aggregates=["debit:sum", "credit:sum"],
        )
        if not result:
            return 0.0
        first_result = result[0]
        debit = first_result[1]
        credit = first_result[2]
        return debit - credit

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
                f"Balance is not {str(expected_balance)} for Purchase "
                f"Line {purchase_line.name}.",
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
        picking.move_ids.write({"quantity": 1.0})
        picking.button_validate()

        bill = (
            self.env["account.move"]
            .with_user(self.purchase_user)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": purchase.partner_id.id,
                    "invoice_date": fields.Date.today(),
                    "purchase_id": purchase.id,  # Link to PO
                }
            )
        )
        bill.invoice_line_ids = [
            Command.create(
                {
                    "product_id": self.product.id,
                    "quantity": 1.0,
                    "price_unit": po_line.price_unit,
                    "purchase_line_id": po_line.id,
                }
            )
        ]
        bill.action_post()

        expected_balance = 500.0
        self._check_account_balance(
            self.account_inventory.id,
            purchase_line=po_line,
            expected_balance=expected_balance,
        )

        for aml in bill.invoice_line_ids:
            if aml.product_id == po_line.product_id and aml.move_id:
                self.assertEqual(
                    aml.purchase_line_id,
                    po_line,
                    "Purchase Order line has not been copied "
                    "from the invoice to the account move line.",
                )

    def test_display_name(self):
        purchase = self._create_purchase([(self.product, 1)])
        po_line = purchase.order_line[0]
        name_get = po_line.with_context(**{"po_line_info": True}).read(["display_name"])
        name_get = [(po_line.id, name_get[0]["display_name"])]
        self.assertEqual(
            name_get,
            [
                (
                    po_line.id,
                    f"[{po_line.order_id.name}] {po_line.name} "
                    f"({po_line.order_id.state})",
                )
            ],
        )
        name_get_no_ctx = po_line.read(["display_name"])
        name_get_no_ctx = [(po_line.id, name_get_no_ctx[0]["display_name"])]
        self.assertEqual(name_get_no_ctx, [(po_line.id, po_line.name)])
