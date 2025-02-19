# Copyright 2020-23 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command
from odoo.tests import common


class TestAccountMoveLineSaleInfo(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_model = cls.env["sale.order"]
        cls.sale_line_model = cls.env["sale.order.line"]
        cls.product_model = cls.env["product.product"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.account_model = cls.env["account.account"]
        cls.aml_model = cls.env["account.move.line"]
        cls.res_users_model = cls.env["res.users"]

        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.company = cls.env.ref("base.main_company")
        cls.group_sale_user = cls.env.ref("sales_team.group_sale_salesman")
        cls.group_account_invoice = cls.env.ref("account.group_account_invoice")
        cls.group_account_manager = cls.env.ref("account.group_account_manager")

        # Create account for Goods Received Not Invoiced
        acc_type = "equity"
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account(acc_type, name, code, cls.company)

        # Create account for Cost of Goods Sold
        acc_type = "expense"
        name = "Cost of Goods Sold"
        code = "cogs"
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Inventory
        acc_type = "asset_fixed"
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(acc_type, name, code, cls.company)
        # Create Product
        cls.product = cls._create_product()

        # Create users
        cls.sale_user = cls._create_user(
            "sale_user",
            [cls.group_sale_user, cls.group_account_invoice],
            cls.company,
        )
        cls.account_invoice = cls._create_user(
            "account_invoice", [cls.group_account_invoice], cls.company
        )
        cls.account_manager = cls._create_user(
            "account_manager", [cls.group_account_manager], cls.company
        )
        cls.JournalObj = cls.env["account.journal"]
        cls.journal_sale = cls.JournalObj.create(
            {
                "name": "Test journal sale",
                "code": "TST-JRNL-S",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

    @classmethod
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

    @classmethod
    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_ids": [Command.set([company.id])],
            }
        )
        return account

    @classmethod
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
                "type": "consu",
                "standard_price": 1.0,
                "list_price": 1.0,
                "is_storable": True,
            }
        )
        return product

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
        return self.sale_model.create(
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

    def _check_account_balance(self, account_id, sale_line=None, expected_balance=0.0):
        """
        Check the balance of the account
        """
        domain = [("account_id", "=", account_id)]
        if sale_line:
            domain.extend([("sale_line_id", "=", sale_line.id)])

        balance = self._get_balance(domain)
        if sale_line:
            self.assertEqual(
                balance,
                expected_balance,
                f"Balance is not {str(expected_balance)} "
                f"for sale Line {sale_line.name}.",
            )

    def move_reversal_wiz(self, move):
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[move.id])
            .create({"journal_id": move.journal_id.id})
        )
        return wizard

    def test_01_sale_invoice(self):
        """Test that the po line moves from the sale order to the
        account move line and to the invoice line.
        """
        sale = self._create_sale([(self.product, 1)])
        so_line = False
        for line in sale.order_line:
            so_line = line
            break
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.move_ids.write({"quantity": 1.0, "picked": True})
        picking.button_validate()

        expected_balance = -1.0
        self._check_account_balance(
            self.account_inventory.id,
            sale_line=so_line,
            expected_balance=expected_balance,
        )
        self.context = {
            "active_model": "sale.order",
            "active_ids": [sale.id],
            "active_id": sale.id,
            "default_journal_id": self.journal_sale.id,
        }
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(**self.context)
            .create({"advance_payment_method": "delivered"})
        )
        payment.create_invoices()
        invoice = sale.invoice_ids[0]
        invoice._post()

        for aml in invoice.line_ids:
            if aml.product_id == so_line.product_id and aml.move_id:
                self.assertEqual(
                    aml.sale_line_id,
                    so_line,
                    "sale Order line has not been copied "
                    "from the invoice to the account move line.",
                )

    def test_02_name_get(self):
        sale = self._create_sale([(self.product, 1)])
        so_line = sale.order_line[0]
        name_get = so_line.with_context(**{"so_line_info": True}).display_name
        self.assertEqual(
            name_get,
            f"[{so_line.order_id.name}] {so_line.product_id.name} - "
            f"({so_line.order_id.state})",
        )
        name_get_no_ctx = so_line.with_context(**{}).display_name
        self.assertEqual(
            name_get_no_ctx,
            f"{so_line.order_id.name} - {so_line.product_id.name} "
            f"{so_line._additional_name_per_id()[so_line.id]}",
        )

    def test_03_credit_note(self):
        """Test the credit note is linked to the sale order line"""
        sale = self._create_sale([(self.product, 1)])
        so_line = False
        for line in sale.order_line:
            so_line = line
            break
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.move_ids.write({"quantity": 1.0, "picked": True})
        picking.button_validate()
        sale._create_invoices()
        invoice = sale.invoice_ids[0]
        invoice._post()
        reversal_wizard = self.move_reversal_wiz(invoice)
        credit_note = self.env["account.move"].browse(
            reversal_wizard.reverse_moves()["res_id"]
        )
        for aml in credit_note.line_ids:
            if aml.product_id == so_line.product_id and aml.move_id:
                self.assertEqual(
                    aml.sale_line_id,
                    so_line,
                    "sale Order line has not been copied "
                    "from the invoice to the credit note.",
                )
