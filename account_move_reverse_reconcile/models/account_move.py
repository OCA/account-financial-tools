# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models

REVERSAL_POST_AUTOMATIC_RECONCILE_VALUES = [
    ("reconcile", "Reconcile"),
    ("full_amount_reconcile", "Reconcile only with full amount"),
    ("no_reconcile", "Do not reconcile"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    reversal_post_automatic_reconcile = fields.Selection(
        REVERSAL_POST_AUTOMATIC_RECONCILE_VALUES,
        compute="_compute_reversal_post_automatic_reconcile",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        copy=False,
        string="Automatic reconciliation on posting of reversal moves",
        help="Defines if the posting of the move must reconcile with its originating "
        "move",
    )

    @api.depends("journal_id")
    def _compute_reversal_post_automatic_reconcile(self):
        for move in self:
            if move.reversal_post_automatic_reconcile or not move.journal_id:
                continue
            move.reversal_post_automatic_reconcile = (
                move.journal_id.reversal_post_automatic_reconcile_default
            )

    def _reconcile_reversed_moves(self, reverse_moves, move_reverse_cancel):
        moves_to_reconcile_ids = list()
        reverse_moves_to_reconcile_ids = list()
        for move, reverse_move in zip(self, reverse_moves, strict=False):
            if reverse_move.reversal_post_automatic_reconcile == "reconcile":
                moves_to_reconcile_ids.append(move.id)
                reverse_moves_to_reconcile_ids.append(reverse_move.id)
            elif (
                reverse_move.reversal_post_automatic_reconcile
                == "full_amount_reconcile"
            ):
                # Reimplement code and conditions from
                #  odoo.addons.account.models.account_move.AccountMove._reconcile_reversed_moves  # noqa
                group = (
                    (move.line_ids + reverse_move.line_ids)
                    .filtered(lambda li: not li.reconciled)
                    .sorted(
                        lambda li: li.account_type
                        not in ("asset_receivable", "liability_payable")
                    )
                    .grouped(lambda li: (li.account_id, li.currency_id))
                )
                for (account, currency), lines in group.items():
                    if (
                        (
                            all(
                                not line.reconciled for line in lines
                            )  # if it was reconciled due to a previous group
                            and account.reconcile
                            or account.account_type
                            in ("asset_cash", "liability_credit_card")
                        )
                        # Add extra condition on the amount
                        and currency.is_zero(sum(line.balance for line in lines))
                    ):
                        moves_to_reconcile_ids.append(move.id)
                        reverse_moves_to_reconcile_ids.append(reverse_move.id)
        moves_to_reconcile = self.browse(moves_to_reconcile_ids)
        reverse_moves_to_reconcile = self.browse(reverse_moves_to_reconcile_ids)
        return super(AccountMove, moves_to_reconcile)._reconcile_reversed_moves(
            reverse_moves_to_reconcile, move_reverse_cancel
        )
