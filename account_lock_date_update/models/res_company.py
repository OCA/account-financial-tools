# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_unreconciled_statement_lines_redirect_action(
        self, unreconciled_statement_lines
    ):
        # In Odoo 19 the core builds this redirect action on
        # account.bank.statement.line, but:
        #   1. the action dict has no "views" key, so the JS _preprocessAction
        #      crashes on `action.views.map(...)` (the action is passed as a raw
        #      dict to doAction() through the RedirectWarning);
        #   2. account.bank.statement.line has no standalone list/form view in
        #      v19 (it _inherits account.move), so even a fixed action would
        #      land on an auto-generated, unusable view.
        # We therefore redirect to the underlying account.move records, reusing
        # the very views the core already uses for its "Draft Entries"
        # redirect, so the user can review/delete the offending entries.
        moves = unreconciled_statement_lines.move_id
        action = {
            "name": self.env._("Unreconciled Transactions"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
            "search_view_id": [
                self.env.ref("account.view_account_move_filter").id,
                "search",
            ],
            "views": [
                [self.env.ref("account.view_move_tree_multi_edit").id, "list"],
                [self.env.ref("account.view_move_form").id, "form"],
            ],
        }
        if len(moves) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": moves.id,
                    "views": [[self.env.ref("account.view_move_form").id, "form"]],
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", moves.ids)],
                }
            )
        return action
