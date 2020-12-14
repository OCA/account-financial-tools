from odoo import models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    def action_open_reconcile(self):
        # Open reconciliation view for bank statements belonging to this journal
        bank_stmt = (
            self.env["account.bank.statement"]
            .search([("journal_id", "in", self.ids)])
            .mapped("line_ids")
        )
        return {
            "type": "ir.actions.client",
            "tag": "bank_statement_reconciliation_view",
            "context": {
                "statement_line_ids": bank_stmt.ids,
                "company_ids": self.mapped("company_id").ids,
            },
        }

    def action_open_reconcile_to_check(self):
        self.ensure_one()
        ids = self.to_check_ids().ids
        action_context = {
            "show_mode_selector": False,
            "company_ids": self.mapped("company_id").ids,
        }
        action_context.update({"suspense_moves_mode": True})
        action_context.update({"statement_line_ids": ids})
        return {
            "type": "ir.actions.client",
            "tag": "bank_statement_reconciliation_view",
            "context": action_context,
        }
