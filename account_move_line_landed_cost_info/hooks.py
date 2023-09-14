# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(
    "Adding stock valuation adjustment line to the account move line"
)


def add_stock_valuation_adjustment_line(env):
    """based on the account_move_line on the landed cost I search for the lines with
    the same product.
    """
    for val_adj_line in env["stock.valuation.adjustment.lines"].search([]):
        landed_cost = val_adj_line.cost_id
        am = landed_cost.account_move_id
        if not am:
            continue
        if len(landed_cost.valuation_adjustment_lines) == 1:
            # if only one adjustment all the journal items are for the same val_adj_line
            _logger.info(
                "Assigning %s for %s to %s"
                % (
                    am.name,
                    val_adj_line.product_id.display_name,
                    val_adj_line.cost_id.name,
                )
            )
            matched_lines = am.line_ids.filtered(lambda l: not l.stock_landed_cost_id)
            if matched_lines:
                env.cr.execute(
                    """UPDATE account_move_line
                SET (stock_valuation_adjustment_line_id, stock_landed_cost_id) = (%s,%s)
                WHERE id in %s""",
                    (
                        val_adj_line.id,
                        landed_cost.id,
                        tuple(am.line_ids.ids),
                    ),
                )
        elif len(landed_cost.valuation_adjustment_lines):
            # We could match by product, but, there may be several adjustment lines
            # for the same product. And qty or the additional value added do not
            # match in a normal case, because the quantities could already leave the
            # company, so it is best to fill the stock landed cost info only
            matched_lines = am.line_ids.filtered(lambda l: not l.stock_landed_cost_id)
            _logger.info(
                "Assigning %s to %s"
                % (
                    am.name,
                    val_adj_line.cost_id.name,
                )
            )
            if matched_lines:
                env.cr.execute(
                    """UPDATE account_move_line
                SET stock_landed_cost_id = %s
                WHERE id in %s""",
                    (
                        landed_cost.id,
                        tuple(matched_lines.ids),
                    ),
                )
            else:
                _logger.info(
                    "Could not match account move line for %s and %s, product %s"
                    % (
                        landed_cost.name,
                        am.name,
                        val_adj_line.product_id.display_name,
                    )
                )


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    add_stock_valuation_adjustment_line(env)
