# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(cr, registry):

    """INIT purchase_line_id in acount move line"""
    # FOR stock moves
    cr.execute(
        """
        UPDATE account_move_line aml SET purchase_line_id = sm.purchase_line_id
        FROM account_move_line aml2
        INNER JOIN account_move am
        ON am.id = aml2.move_id
        INNER JOIN stock_move sm ON
        am.stock_move_id = sm.id
        WHERE aml.id = aml2.id
        AND sm.purchase_line_id IS NOT NULL;
    """
    )
