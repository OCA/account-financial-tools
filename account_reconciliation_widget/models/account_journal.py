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
