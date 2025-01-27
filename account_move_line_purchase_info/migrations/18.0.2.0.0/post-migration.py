import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    purchase_orders = env["purchase.order"].search([("state", "=", "purchase")])
    for order in purchase_orders:
        try:
            _logger.info(f"Processing Purchase Order: {order.name} (ID: {order.id})")
            valued_lines = order.order_line.invoice_lines.filtered(
                lambda line: line.product_id
                and line.product_id.cost_method != "standard"
                and (
                    not line.company_id.tax_lock_date
                    or line.date > line.company_id.tax_lock_date
                )
            )
            svls, _amls = valued_lines._apply_price_difference()

            if svls:
                svls._validate_accounting_entries()

            bills = order.invoice_ids.filtered(lambda bill: bill.state == "posted")
            bills._stock_account_anglo_saxon_reconcile_valuation()

        except Exception as e:
            _logger.error(
                (
                    f"Error processing Purchase Order {order.name} "
                    f"(ID: {order.id}): {str(e)}"
                ),
                exc_info=True,
            )
