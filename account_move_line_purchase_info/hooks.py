# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import ast
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):

    """ INIT purchase references in acount move line """
    # FOR stock moves
    cr.execute("""
        update account_move_line aml set purchase_line_id = sm.purchase_line_id
        FROM account_move_line aml2
        INNER JOIN stock_move sm ON
        aml2.stock_move_id = sm.id
        WHERE aml.id = aml2.id;
    """)
    # FOR invoices
    cr.execute("""
        update account_move_line aml set purchase_line_id = pol.id
        FROM account_move_line aml2
        INNER JOIN account_invoice ai ON
        ai.id = aml2.invoice_id
        INNER JOIN account_invoice_line ail ON
        ail.invoice_id = ai.id
        INNER JOIN purchase_order_line pol ON
        ail.purchase_line_id = pol.id
        WHERE aml.id = aml2.id;
    """)

    # NOW we can fill the PO
    cr.execute("""
        UPDATE account_move_line aml
        SET purchase_id = pol.order_id
        FROM purchase_order_line AS pol
        WHERE aml.purchase_line_id = pol.id
    """)
