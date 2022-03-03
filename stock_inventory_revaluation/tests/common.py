# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.stock_account.tests.test_anglo_saxon_valuation_reconciliation_common import (
    ValuationReconciliationTestCommon,
)


class TestStockInventoryRevaluationCommon(ValuationReconciliationTestCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        # Objects
        cls.Product = cls.env["product.product"]
        cls.Picking = cls.env["stock.picking"]
        cls.Move = cls.env["stock.move"]
        cls.partner_model = cls.env["res.partner"]
        cls.account_move_model = cls.env["account.move"]
        cls.account_move_line_model = cls.env["account.move.line"]
        cls.revaluation_model = cls.env["stock.inventory.revaluation"]
        cls.revaluation_line_model = cls.env["stock.inventory.revaluation.line"]
        # References and Base records
        cls.EUR = cls.env.ref("base.EUR")
        cls.USD = cls.env.ref("base.USD")
        cls.warehouse = cls.company_data["default_warehouse"]
        cls.supplier_id = cls.env["res.partner"].create({"name": "My Test Supplier"}).id
        cls.customer_id = cls.env["res.partner"].create({"name": "My Test Customer"}).id
        cls.supplier_location_id = cls.env.ref("stock.stock_location_suppliers").id
        cls.customer_location_id = cls.env.ref("stock.stock_location_customers").id
        cls.categ_all = cls.stock_account_product_categ
        cls.company_data.update(
            {
                "default_account_stock_expense": cls.env["account.account"].create(
                    {
                        "name": "default_account_stock_expenses",
                        "code": "EXPEXPENSES",
                        "reconcile": True,
                        "user_type_id": cls.env.ref(
                            "account.data_account_type_expenses"
                        ).id,
                        "company_id": cls.company_data["company"].id,
                    }
                )
            }
        )
        cls.categ_manual_periodic = cls.env.ref("product.product_category_all").copy(
            {"property_valuation": "manual_periodic"}
        )
        cls.categ_real_time_fifo = cls.stock_account_product_categ.copy(
            {
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_valuation_account_id": cls.company_data[
                    "default_account_stock_valuation"
                ].id,
                "property_stock_account_input_categ_id": cls.company_data[
                    "default_account_stock_in"
                ].id,
                "property_stock_account_output_categ_id": cls.company_data[
                    "default_account_stock_out"
                ].id,
                "property_account_expense_categ_id": cls.company_data[
                    "default_account_stock_expense"
                ].id,
            }
        )
        cls.categ_real_time_avg = cls.stock_account_product_categ.copy(
            {
                "property_valuation": "real_time",
                "property_cost_method": "average",
                "property_stock_valuation_account_id": cls.company_data[
                    "default_account_stock_valuation"
                ].id,
                "property_stock_account_input_categ_id": cls.company_data[
                    "default_account_stock_in"
                ].id,
                "property_stock_account_output_categ_id": cls.company_data[
                    "default_account_stock_out"
                ].id,
                "property_account_expense_categ_id": cls.company_data[
                    "default_account_stock_expense"
                ].id,
            }
        )
        cls.expenses_journal = cls.company_data["default_journal_purchase"]
        cls.stock_journal = cls.env["account.journal"].create(
            {
                "name": "Stock Journal",
                "code": "STJTEST",
                "type": "general",
            }
        )
        cls.env.company.anglo_saxon_accounting = True
        # Variables
        cls.frozen_today = fields.Date.today()

    @classmethod
    def _create_product(cls, name, cost, category):
        """Create a new storable product
        :param name:                The string with the name
        :param cost:                The standard price
        :param category:            The product category object
        :return:                    The newly created product.
        """
        pp = cls.Product.create(
            {
                "name": name,
                "type": "product",
                "standard_price": cost,
                "categ_id": category.id,
            }
        )
        return pp

    @classmethod
    def _create_bill(
        cls, inv_type, vendor, products, quantities, prices, currency=False
    ):
        """Create a new vendor bill with one product
        :param inv_type             The type of invoice(default is 'in_invoice')
        :param vendor:              The vendor to set on the invoice.
        :param products:            List with product.product
        :param quantities:          List with quantities by line
        :param prices:              List with prices by line
        :return:                    The newly created vendor bill.
        """
        if inv_type not in ("in_invoice", "in_refund", "out_invoice", "out_refund"):
            inv_type = "in_invoice"
        invoice_form = Form(
            cls.account_move_model.with_context(default_move_type=inv_type)
        )
        invoice_form.partner_id = vendor
        invoice_form.invoice_date = cls.frozen_today
        if currency:
            invoice_form.currency_id = currency
        for product, qty, price in zip(products, quantities, prices):
            with invoice_form.invoice_line_ids.new() as invoice_line_form:
                # Set the default account to avoid "account_id is a required field"
                # in case of bad configuration.
                invoice_line_form.name = product.name
                invoice_line_form.product_id = product
                invoice_line_form.account_id = (
                    product.categ_id.property_stock_account_input_categ_id
                )
                invoice_line_form.quantity = qty
                invoice_line_form.price_unit = price
        invoice = invoice_form.save()
        return invoice

    @classmethod
    def _do_picking(cls, picking):
        """Mark all qties as done and validate the picking"""
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_lines:
            ml.filtered(
                lambda m: m.state != "waiting"
            ).quantity_done = ml.product_uom_qty
        picking.button_validate()

    @classmethod
    def _create_picking(cls, picking_type_id, moves):
        """Create a new picking
        :param picking_type_id:     The id of the picking type
        :param moves:               The list with tuples (0,0, vals)
            :vals product           The product object
            :vals qty               The quantity in the stock move
            :vals location_id       The id of the source location
            :vals location_dest_id  The id of the destination location
        :return:                    The newly created picking.
        """
        picking_default_vals = cls.env["stock.picking"].default_get(
            list(cls.env["stock.picking"].fields_get())
        )
        move_vals = []
        for move in moves:
            move_vals.append(
                (
                    0,
                    0,
                    {
                        "product_id": move["product"].id,
                        "product_uom_qty": move["qty"],
                        "product_uom": move["product"].uom_id.id,
                        "location_id": move["location_id"],
                        "location_dest_id": move["location_dest_id"],
                    },
                )
            )
        vals = dict(
            picking_default_vals,
            **{
                "picking_type_id": picking_type_id,
                "move_lines": move_vals,
            }
        )
        picking_to_revaluate_1 = cls.env["stock.picking"].new(vals)
        picking_to_revaluate_1.onchange_picking_type()
        for ml in picking_to_revaluate_1.move_lines:
            ml.onchange_product_id()
        vals = picking_to_revaluate_1._convert_to_write(picking_to_revaluate_1._cache)
        return cls.Picking.create(vals)

    @classmethod
    def _create_currency_rate(cls, currency_id, name, rate):
        cls.env["res.currency.rate"].create(
            {"currency_id": currency_id.id, "name": name, "rate": rate}
        )
