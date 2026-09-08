# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    """Back-fill repair_order_id on invoice AMLs linked to repairs via SOs.

    The mapping mirrors ``sale.order.line._prepare_invoice_line``: the repair
    order is first resolved per sale order line through its stock moves and,
    when that is not conclusive, through the sale order itself. In both cases
    ambiguous matches (more than one repair order) are skipped.
    """
    env.cr.execute(
        """
        UPDATE account_move_line aml
           SET repair_order_id = sml.repair_id
          FROM sale_order_line_invoice_rel rel
          JOIN (
                  SELECT sm.sale_line_id, MIN(sm.repair_id) AS repair_id
                    FROM stock_move sm
                   WHERE sm.repair_id IS NOT NULL
                     AND sm.sale_line_id IS NOT NULL
                   GROUP BY sm.sale_line_id
                  HAVING COUNT(DISTINCT sm.repair_id) = 1
               ) sml ON sml.sale_line_id = rel.order_line_id
         WHERE aml.id              = rel.invoice_line_id
           AND aml.repair_order_id IS NULL;
        """
    )
    env.cr.execute(
        """
        UPDATE account_move_line aml
           SET repair_order_id = ro.repair_id
          FROM sale_order_line_invoice_rel rel
          JOIN sale_order_line sol ON sol.id = rel.order_line_id
          JOIN (
                  SELECT sale_order_id, MIN(id) AS repair_id
                    FROM repair_order
                   WHERE sale_order_id IS NOT NULL
                   GROUP BY sale_order_id
                  HAVING COUNT(*) = 1
               ) ro ON ro.sale_order_id = sol.order_id
         WHERE aml.id              = rel.invoice_line_id
           AND aml.repair_order_id IS NULL;
        """
    )
    # Anglo-saxon COGS lines are not part of the sale order line relation, so
    # they are back-filled from the invoice line they originate from.
    env.cr.execute(
        """
        UPDATE account_move_line aml
           SET repair_order_id = origin.repair_order_id
          FROM account_move_line origin
         WHERE aml.cogs_origin_id     = origin.id
           AND aml.repair_order_id   IS NULL
           AND origin.repair_order_id IS NOT NULL;
        """
    )
