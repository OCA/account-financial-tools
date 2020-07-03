# -*- coding: utf-8 -*-
# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging


logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, if a database has a few hundred thousand
    move lines, which is not unlikely, the update will take
    at least a few hours.

    The pre init script pre-computes the field using SQL.
    """
    store_field_purchase_id(cr)
    store_field_purchase_line_id(cr)


def store_field_purchase_id(cr):

    cr.execute(
        """SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='purchase_id'"""
    )
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN purchase_id integer;
            COMMENT ON COLUMN account_move_line.purchase_id
            IS 'Purchase Order';
            """
        )

    logger.info("Computing field purchase_id on account.move.line")


def store_field_purchase_line_id(cr):

    cr.execute(
        """SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='purchase_line_id'"""
    )
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN purchase_line_id integer;
            COMMENT ON COLUMN account_move_line.purchase_line_id
            IS 'Purchase Order Line';
            """
        )

    logger.info("Computing field purchase_line_id on account.move.line")
