# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import common


class TestAccountMoveLineSaleInfo(common.TransactionCase):
    def setUp(self):
        super(TestAccountMoveLineSaleInfo, self).setUp()
        self.sale_model = self.env["sale.order"]
        self.sale_line_model = self.env["sale.order.line"]
        self.product_model = self.env["product.product"]
        self.product_ctg_model = self.env["product.category"]
        self.acc_type_model = self.env["account.account.type"]
        self.account_model = self.env["account.account"]
        self.aml_model = self.env["account.move.line"]
        self.res_users_model = self.env["res.users"]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.location_stock = self.env.ref("stock.stock_location_stock")
        self.company = self.env.ref("base.main_company")
        self.group_sale_user = self.env.ref("sales_team.group_sale_salesman")
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
        self.sale_user = self._create_user(
            "sale_user",
            [self.group_sale_user, self.group_account_invoice],
            self.company,
        )
        self.account_invoice = self._create_user(
            "account_invoice", [self.group_account_invoice], self.company
        )
        self.account_manager = self._create_user(
            "account_manager", [self.group_account_manager], self.company
        )
        self.JournalObj = self.env["account.journal"]
        self.journal_sale = self.JournalObj.create(
            {
                "name": "Test journal sale",
                "code": "TST-JRNL-S",
                "type": "sale",
                "company_id": self.company.id,
            }
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

    def _create_account_type(self, name, atype):
        acc_type = self.acc_type_model.create(
            {"name": name, "type": atype, "internal_group": name}
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
                "Balance is not %s for sale Line %s."
                % (str(expected_balance), sale_line.name),
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
        picking.move_lines.write({"quantity_done": 1.0})
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
        name_get = so_line.with_context(**{"so_line_info": True}).name_get()
        self.assertEqual(
            name_get,
            [
                (
                    so_line.id,
                    "[%s] %s - (%s)"
                    % (
                        so_line.order_id.name,
                        so_line.product_id.name,
                        so_line.order_id.state,
                    ),
                )
            ],
        )
        name_get_no_ctx = so_line.with_context(**{}).name_get()
        self.assertEqual(
            name_get_no_ctx,
            [
                (
                    so_line.id,
                    "{} - {}".format(so_line.order_id.name, so_line.product_id.name),
                )
            ],
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
        picking.move_lines.write({"quantity_done": 1.0})
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
