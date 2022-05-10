# Copyright 2021 Carlos Lopez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(cr, registry):

    """ INIT purchase references in acount move line """
    # FOR stock moves
    cr.execute(
        """
        UPDATE account_move_line aml
            SET purchase_line_id = sm.purchase_line_id, purchase_id = pol.order_id
        FROM stock_move sm
            INNER JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
            INNER JOIN account_move am ON am.stock_move_id  = sm.id
        WHERE am.id = aml.move_id AND sm.purchase_line_id IS NOT NULL;
    """
    )
