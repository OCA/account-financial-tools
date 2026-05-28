# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Backfill oca_purchase_line_id on anglo-saxon price-difference COGS
    lines that the previous implementation left empty on vendor bills.

    Mirrors the per-move pair-aware logic now used in
    AccountMove._stock_account_prepare_anglo_saxon_in_lines_vals
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    move_groups = env["account.move.line"].read_group(
        domain=[
            ("display_type", "=", "cogs"),
            ("oca_purchase_line_id", "=", False),
            (
                "move_id.move_type",
                "in",
                ("in_invoice", "in_refund", "in_receipt"),
            ),
            ("company_id.anglo_saxon_accounting", "=", True),
        ],
        fields=["move_id"],
        groupby=["move_id"],
    )
    if not move_groups:
        return
    move_ids = [g["move_id"][0] for g in move_groups]
    moves = env["account.move"].browse(move_ids)
    _logger.info(
        "account_move_line_purchase_info: backfilling oca_purchase_line_id "
        "on COGS lines for %s moves",
        len(moves),
    )
    updated = 0
    for move in moves:
        broken = move.line_ids.filtered(
            lambda l: l.display_type == "cogs" and not l.oca_purchase_line_id
        )
        # Respect any POL already linked to other COGS
        # lines in the move
        consumed = set(
            move.line_ids.filtered(
                lambda l: l.display_type == "cogs" and l.oca_purchase_line_id
            )
            .mapped("oca_purchase_line_id")
            .ids
        )
        # First group COGS pair lines by product and qty
        groups_by_pq = {}
        for cogs in broken:
            key = (cogs.product_id.id, cogs.quantity)
            groups_by_pq.setdefault(key, env["account.move.line"])
            groups_by_pq[key] |= cogs
        # For each product/qty group, assign POL candidates
        for (product_id, quantity), group in groups_by_pq.items():
            # Standard-cost price-diff rows set quantity to the relevant
            # qty; FIFO/AVCO rows from _prepare_pdiff_aml_vals leave it at
            # 0. In the latter case, match candidate invoice lines by
            # product only so we don't filter every line out.
            candidates = move.invoice_line_ids.filtered(
                lambda il: il.product_id.id == product_id
                and (not quantity or il.quantity == quantity)
            ).mapped("purchase_line_id")
            available = [pol for pol in candidates if pol.id not in consumed]
            if not available:
                continue
            # Within a (product, qty) group each invoice line produced
            # one price-diff row + one stock-input correction row
            # Pair them by creation order (id ASC) and
            # assign one available POL per pair
            accounts = group.mapped("account_id")
            if len(accounts) != 2:
                _logger.warning(
                    "Skipping move %s product %s qty %s: expected 2 "
                    "distinct COGS pair accounts, found %s",
                    move.id,
                    product_id,
                    quantity,
                    len(accounts),
                )
                continue
            rows_a = group.filtered(lambda l: l.account_id == accounts[0]).sorted("id")
            rows_b = group.filtered(lambda l: l.account_id == accounts[1]).sorted("id")
            if len(rows_a) != len(rows_b):
                _logger.warning(
                    "Skipping move %s product %s qty %s: unbalanced "
                    "COGS rows (%s vs %s)",
                    move.id,
                    product_id,
                    quantity,
                    len(rows_a),
                    len(rows_b),
                )
                continue
            pair_count = min(len(rows_a), len(available))
            for i in range(pair_count):
                pol_id = available[i].id
                (rows_a[i] + rows_b[i]).with_context(check_move_validity=False).write(
                    {"oca_purchase_line_id": pol_id}
                )
                consumed.add(pol_id)
                updated += 2
    _logger.info(
        "account_move_line_purchase_info: backfilled oca_purchase_line_id "
        "on %s COGS lines",
        updated,
    )
