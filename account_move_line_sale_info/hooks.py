# -*- coding: utf-8 -*-
# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging


logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """ INIT sale references in acount move line """
    # FOR stock moves
    cr.execute("""
        update account_move_line aml set sale_line_id = proc.sale_line_id
        FROM account_move_line aml2
        INNER JOIN stock_move sm ON
        aml2.stock_move_id = sm.id
        INNER JOIN procurement_order proc ON
        sm.procurement_id = proc.id
        WHERE aml.id = aml2.id;
    """)
    # FOR invoices
    cr.execute("""
        update account_move_line aml set sale_line_id = sol.id
        FROM account_move_line aml2
        INNER JOIN account_invoice ai ON
        ai.id = aml2.invoice_id
        INNER JOIN account_invoice_line ail ON
        ail.invoice_id = ai.id
        INNER JOIN sale_order_line_invoice_rel rel ON
        rel.invoice_line_id = ail.id
        INNER JOIN sale_order_line sol ON
        rel.order_line_id = sol.id
        AND sol.product_id = aml2.product_id
        WHERE aml.id = aml2.id;
    """)

    # NOW we can fill the SO
    cr.execute("""
        UPDATE account_move_line aml
        SET sale_id = sol.order_id
        FROM sale_order_line AS sol
        WHERE aml.sale_line_id = sol.id;
    """)

    # NOW we can fill the lines without invoice_id (Odoo put it very
    # complicated)

    cr.execute("""
        UPDATE account_move_line aml
        SET sale_id = so.id
        FROM sale_order_line so
        LEFT JOIN account_move_line aml2
        ON aml2.sale_id = so.id
        WHERE aml2.move_id = aml.move_id;
    """)

    cr.execute("""
        update account_move_line aml set sale_line_id = sol.id
        FROM account_move_line aml2
        INNER JOIN sale_order so ON
        so.id = aml2.sale_id
        INNER JOIN sale_order_line sol ON
        so.id = sol.order_id
        AND sol.product_id = aml2.product_id
        WHERE aml.id = aml2.id;
    """)


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, if a database has a few hundred thousand
    move lines, which is not unlikely, the update will take
    at least a few hours.

    The pre init script pre-computes the field using SQL.
    """
    store_field_sale_id(cr)
    store_field_sale_line_id(cr)


def store_field_sale_id(cr):

    cr.execute(
        """SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='sale_id'"""
    )
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN sale_id integer;
            COMMENT ON COLUMN account_move_line.sale_id
            IS 'Sale Order';
            """
        )

    logger.info("Computing field sale_id on account.move.line")


def store_field_sale_line_id(cr):

    cr.execute(
        """SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='sale_line_id'"""
    )
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN sale_line_id integer;
            COMMENT ON COLUMN account_move_line.sale_line_id
            IS 'Sale Order Line';
            """
        )

    logger.info("Computing field sale_line_id on account.move.line")
