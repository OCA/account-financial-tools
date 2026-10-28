# Copyright 2019-23 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    """INIT sale references in account move line"""
    # FOR stock moves
    env.cr.execute(
        """
        UPDATE account_move_line aml SET sale_line_id = sm.sale_line_id
        FROM stock_move sm
        WHERE sm.account_move_id = aml.move_id
        AND sm.product_id = aml.product_id
        AND sm.sale_line_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM stock_move sm2
            WHERE sm2.account_move_id = sm.account_move_id
            AND sm2.product_id = sm.product_id
            AND sm2.id != sm.id
        );
    """
    )
    # FOR invoices
    env.cr.execute(
        """
        UPDATE account_move_line aml SET sale_line_id = sol.id
        FROM account_move_line aml2
        INNER JOIN account_move am ON
        am.id = aml2.move_id
        INNER JOIN sale_order_line_invoice_rel rel ON
        rel.invoice_line_id = aml2.id
        INNER JOIN sale_order_line sol ON
        rel.order_line_id = sol.id
        AND sol.product_id = aml2.product_id
        WHERE aml.id = aml2.id;
    """
    )

    # FOR cost of goods sold lines
    env.cr.execute(
        """
        UPDATE account_move_line aml SET sale_line_id = origin.sale_line_id
        FROM account_move_line origin
        WHERE aml.cogs_origin_id = origin.id
        AND origin.sale_line_id IS NOT NULL;
    """
    )

    # NOW we can fill the SO
    env.cr.execute(
        """
        UPDATE account_move_line aml
        SET sale_order_id = sol.order_id
        FROM sale_order_line AS sol
        WHERE aml.sale_line_id = sol.id
        RETURNING aml.move_id
    """
    )
